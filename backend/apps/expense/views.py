import pytz
from apps.expense.imports import ExpenseManager
from apps.richtato_user.utils import (
    _get_line_graph_data_by_day,
    _get_line_graph_data_by_month,
)
from apps.settings.models import CardAccount, Category
from artificial_intelligence.ai import OpenAI
from django.db.models import F
from django.shortcuts import get_object_or_404
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
from statement_imports.ocr.extract import (
    extract_statement_to_df,
    map_raw_table_to_standard,
)

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
        limit_param = request.GET.get("limit", None)

        try:
            limit = int(limit_param) if limit_param is not None else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        entries = (
            Expense.objects.filter(user=request.user)
            .annotate(
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
        # HACK
        modified_data = request.data.copy()
        modified_data["account_name"] = modified_data.pop("Account", None)
        modified_data["category"] = modified_data.pop("Category", None)
        modified_data["user"] = request.user.id
        logger.debug(f"Modified data: {modified_data}")

        serializer = ExpenseSerializer(data=modified_data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
        reversed_data = self.apply_fieldmap(request.data)
        logger.debug(f"Reversed data: {reversed_data}")
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
        user_card_accounts = CardAccount.objects.filter(user=request.user)
        user_categories = Category.objects.filter(user=request.user)
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


class CategorizeTransactionView(APIView):
    permission_classes = [IsAuthenticated]

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
        category = OpenAI().categorize_transaction(request.user, description)

        cateogry_id = Category.objects.filter(name=category).first().id
        logger.debug(f"Categorized as: {category}")
        return Response({"category": cateogry_id})


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
            is_pdf = name_lower.endswith(".pdf")
            is_image = name_lower.endswith((".jpg", ".jpeg", ".png", ".heic", ".heif"))

            if is_pdf or is_image:
                # OCR path: save to temp, extract, map, and import
                tmp_path = _save_uploaded_to_temp(file)
                try:
                    raw_df = extract_statement_to_df(tmp_path)
                    std_df = map_raw_table_to_standard(raw_df, card.name)
                    if std_df is not None and not std_df.empty:
                        ExpenseManager.import_from_dataframe(std_df, request.user)
                    else:
                        logger.warning("OCR produced no usable rows; skipping file")
                finally:
                    try:
                        import os

                        os.remove(tmp_path)
                    except Exception:
                        pass
            else:
                # Fall back to existing CSV/XLSX canonicalizers
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
