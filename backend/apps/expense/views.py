import pytz
from apps.expense.imports import ExpenseManager
from apps.richtato_user.models import CardAccount, Category
from apps.richtato_user.utils import (
    _get_line_graph_data_by_day,
    _get_line_graph_data_by_month,
)
from artificial_intelligence.ai import OpenAI
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from richtato.views import BaseAPIView
from statement_imports.cards.card_factory import CardStatement

from .models import Expense
from .serializers import ExpenseSerializer

pst = pytz.timezone("US/Pacific")


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class ExpenseAPIView(BaseAPIView):
    @property
    def field_remap(self):
        return {
            "Account": "account_name__name",
            "Category": "category__name",
        }

    @swagger_auto_schema(
        operation_summary="Get expense entries",
        operation_description="Retrieve expense entries for the authenticated user",
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Limit number of results",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"columns": [], "rows": []}}
            )
        },
    )
    def get(self, request):
        """
        Get the most recent entries for the user.
        """
        from datetime import datetime as _dt

        limit_param = request.GET.get("limit", None)
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        try:
            limit = int(limit_param) if limit_param is not None else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        # Build base queryset
        qs = Expense.objects.filter(user=request.user)

        # Optional date filtering
        try:
            if start_date_str:
                start_date = _dt.strptime(start_date_str, "%Y-%m-%d").date()
                qs = qs.filter(date__gte=start_date)
            if end_date_str:
                end_date = _dt.strptime(end_date_str, "%Y-%m-%d").date()
                qs = qs.filter(date__lte=end_date)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
            )

        entries = (
            qs.annotate(
                Account=F("account_name__name"),
                Category=F("category__name"),
            )
            .order_by("-date")
            .values(
                "id",
                "date",
                "description",
                "amount",
                "Account",
                "Category",
            )
        )

        if limit is not None:
            logger.debug(f"Limit: {limit}")
            entries = entries[:limit]

        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "description", "title": "Description"},
                {"field": "amount", "title": "Amount"},
                {"field": "Account", "title": "Account"},
                {"field": "Category", "title": "Category"},
            ],
            "rows": entries,
        }
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Create expense entry",
        operation_description="Create a new expense entry for the authenticated user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Expense amount"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Expense description"
                ),
                "date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Expense date",
                ),
                "category": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Category ID"
                ),
                "account_name": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Account ID"
                ),
                "details": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Arbitrary structured metadata (e.g., OCR results)",
                ),
            },
            required=["amount", "description", "date"],
        ),
        responses={
            201: openapi.Response("Created"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        """
        Create a new expense entry.
        """
        logger.debug(f"Request data: {request.data}")
        modified_data = request.data.copy()
        # Deprecate name-based fields; enforce ID usage only
        if any(k in modified_data for k in ("Account", "Category")):
            return Response(
                {
                    "error": "Deprecated fields. Use integer IDs only.",
                    "details": {
                        "account_name": "CardAccount ID (required)",
                        "category": "Category ID (optional)",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Attach user for serializer validation
        modified_data["user"] = request.user.id
        logger.debug(f"Normalized data: {modified_data}")
        # Support both account_name and account_id keys (prefer account_name)
        account_id = modified_data.get("account_name") or modified_data.get(
            "account_id"
        )
        category_id = modified_data.get("category") or modified_data.get("category_id")

        if account_id is None:
            return Response(
                {"account_name": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Coerce IDs to int and validate ownership
        try:
            account_id = int(account_id)
        except (TypeError, ValueError):
            return Response(
                {"account_name": ["Must be an integer ID."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not CardAccount.objects.filter(id=account_id, user=request.user).exists():
            return Response(
                {"account_name": ["Account not found for user."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if category_id is not None:
            try:
                category_id = int(category_id)
            except (TypeError, ValueError):
                return Response(
                    {"category": ["Must be an integer ID."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not Category.objects.filter(id=category_id, user=request.user).exists():
                return Response(
                    {"category": ["Category not found for user."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Normalize payload for serializer
        modified_data["account_name"] = account_id
        if category_id is not None:
            modified_data["category"] = category_id

        logger.debug(f"Modified data: {modified_data}")
        try:
            print(
                "[ExpensePOST] Payload",
                {
                    k: (v if k != "details" else "<details>")
                    for k, v in modified_data.items()
                },
            )
        except Exception:
            pass

        serializer = ExpenseSerializer(data=modified_data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        try:
            print("[ExpensePOST] Serializer errors", serializer.errors)
        except Exception:
            pass
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update expense entry",
        operation_description="Update an existing expense entry",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Expense amount"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Expense description"
                ),
                "date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Expense date",
                ),
                "category": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Category ID"
                ),
                "account_name": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Account ID"
                ),
                "details": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Arbitrary structured metadata (e.g., OCR results)",
                ),
            },
        ),
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
            404: openapi.Response("Not Found"),
        },
    )
    def patch(self, request, pk):
        """
        Update an existing expense entry.
        """
        logger.debug(f"PATCH request data: {request.data}")
        # Enforce ID-based updates only
        if any(k in request.data for k in ("Account", "Category")):
            return Response(
                {
                    "error": "Deprecated fields. Use integer IDs only.",
                    "details": {
                        "account_name": "CardAccount ID",
                        "category": "Category ID",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        reversed_data = request.data
        expense = get_object_or_404(Expense, pk=pk, user=request.user)

        serializer = ExpenseSerializer(expense, data=reversed_data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete expense entry",
        operation_description="Delete an existing expense entry",
        responses={
            204: openapi.Response("No Content"),
            404: openapi.Response("Not Found"),
        },
    )
    def delete(self, request, pk):
        """
        Delete an existing expense entry.
        """
        logger.debug(f"DELETE request for expense with pk: {pk}")
        expense = get_object_or_404(Expense, pk=pk, user=request.user)

        expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExpenseGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get expense graph data",
        operation_description="Get expense data for chart visualization",
        manual_parameters=[
            openapi.Parameter(
                "range",
                openapi.IN_QUERY,
                description="Date range: '30d' for last 30 days, 'all' for all time",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"labels": [], "datasets": []}}
            )
        },
    )
    def get(self, request):
        date_range = request.query_params.get("range", "all")
        logger.debug(f"Date range: {date_range}")

        if date_range == "all":
            chart_data = _get_line_graph_data_by_month(request.user, Expense)
        elif date_range == "30d":
            logger.debug("Getting data for the last 30 days")
            chart_data = _get_line_graph_data_by_day(request.user, Expense)
        else:
            return Response({"error": "Invalid range. Use '30d' or 'all'."}, status=400)

        return Response(
            {
                "labels": chart_data["labels"],
                "datasets": [
                    {
                        "label": "Expense",
                        "data": chart_data["values"],
                        "backgroundColor": "rgba(232, 82, 63, 0.2)",
                        "borderColor": "rgba(232, 82, 63, 1)",
                        "borderWidth": 1,
                    }
                ],
            }
        )


class ExpenseFieldChoicesView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get expense field choices",
        operation_description="Get available field choices for expense creation/editing",
        responses={
            200: openapi.Response(
                "Success",
                examples={"application/json": {"account": [], "category": []}},
            )
        },
    )
    def get(self, request):
        user_card_accounts = CardAccount.objects.filter(user=request.user).order_by(
            "name"
        )
        user_categories = Category.objects.filter(user=request.user).order_by("name")
        data = {
            "account": [
                {"value": account.id, "label": account.name}
                for account in user_card_accounts
            ],
            "category": [
                {"value": category.id, "label": category.name}
                for category in user_categories
            ],
        }
        return Response(data)


@method_decorator(csrf_exempt, name="dispatch")
class CategorizeTransactionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    @swagger_auto_schema(
        operation_summary="Categorize transaction",
        operation_description="Use AI to categorize a transaction based on its description",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Transaction description"
                ),
            },
            required=["description"],
        ),
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        """
        Categorize a transaction based on the description.
        """
        description = request.data.get("description")
        if not description:
            return Response({"error": "Description is required."}, status=400)

        # Use AI to categorize the transaction
        try:
            category_name = OpenAI().categorize_transaction(request.user, description)
        except Exception as e:
            logger.exception(f"AI categorize failed, falling back to 'Unknown': {e}")
            category_name = "Unknown"
        # Resolve to a Category ID for this user, with safe fallbacks
        category_obj = (
            Category.objects.filter(user=request.user, name=category_name).first()
            or Category.objects.filter(
                user=request.user, name__iexact=category_name
            ).first()
            or Category.objects.filter(user=request.user, name="Unknown").first()
        )
        if category_obj is None:
            # As an ultimate fallback, create Unknown for the user (should normally exist)
            category_obj = Category.objects.create(user=request.user, name="Unknown")
        logger.debug(f"Categorized as: {category_name} -> id={category_obj.id}")
        return Response({"category": category_obj.id})


class ImportStatementsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Import statements",
        operation_description="Import bank statements and categorize transactions",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "files": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_FILE),
                    description="Statement files",
                ),
                "card_accounts": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Card account IDs",
                ),
            },
            required=["files", "card_accounts"],
        ),
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        """
        Import statements and categorize transactions.
        """

        # Assuming the request contains a file with transactions
        def ensure_list(obj):
            if obj is None:
                return []
            if isinstance(obj, list):
                return obj
            return [obj]

        # Usage
        files = ensure_list(request.FILES.getlist("files"))  # For files specifically
        card_accounts = ensure_list(request.data.getlist("card_accounts"))
        logger.debug(f"Files: {files}")
        logger.debug(f"Card Accounts: {card_accounts}")

        # Helper to persist uploaded file to a temporary path if needed
        def _save_uploaded_to_temp(uploaded_file):
            import os
            import tempfile

            suffix = ""
            try:
                name = getattr(uploaded_file, "name", "") or ""
                _, ext = os.path.splitext(name)
                suffix = ext if ext else ""
            except Exception:
                suffix = ""

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            for chunk in (
                uploaded_file.chunks()
                if hasattr(uploaded_file, "chunks")
                else [uploaded_file.read()]
            ):
                tmp.write(chunk)
            tmp.flush()
            tmp.close()
            return tmp.name

        # Process the files and categorize transactions
        for file, card_account in zip(files, card_accounts):
            card = CardAccount.objects.get(id=card_account, user=request.user)
            logger.debug(f"Card: {card}")
            name_lower = (getattr(file, "name", "") or "").lower()

            # Only support CSV/XLSX files now
            if not (name_lower.endswith((".csv", ".xlsx", ".xls"))):
                logger.warning(
                    f"Unsupported file type: {name_lower}. Only CSV and XLSX files are supported."
                )
                continue

            # Use existing CSV/XLSX canonicalizers
            card_statement = CardStatement.create_from_file(
                request.user,
                card.bank,
                card.name,
                file,
            )
            logger.debug("Card Statement formatted")
            ExpenseManager.import_from_dataframe(
                card_statement.formatted_df, request.user
            )

        return Response({"message": "File processed successfully."})
