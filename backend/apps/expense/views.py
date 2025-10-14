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
    extract_receipt_fields,
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
        try:
            print(
                "[ExpensePOST] Incoming",
                {
                    "user": getattr(request.user, "id", None),
                    "data": dict(request.data),
                },
            )
        except Exception:
            pass
        incoming = request.data.copy()
        account_value = incoming.pop("Account", None)
        category_value = incoming.pop("Category", None)

        try:
            print(
                "[ExpensePOST] Raw Account/Category",
                {"Account": account_value, "Category": category_value},
            )
        except Exception:
            pass

        # Resolve account by id or name (scoped to user)
        account_obj = None
        if account_value is not None:
            try:
                # Try as ID first
                account_obj = CardAccount.objects.get(
                    id=int(account_value), user=request.user
                )
            except Exception:
                # Fallback by name
                account_obj = CardAccount.objects.filter(
                    name=str(account_value), user=request.user
                ).first()

        try:
            print(
                "[ExpensePOST] Resolved Account",
                {
                    "found": bool(account_obj),
                    "id": getattr(account_obj, "id", None),
                    "name": getattr(account_obj, "name", None),
                },
            )
        except Exception:
            pass

        # If an account was provided but couldn't be resolved, return a clear error
        if account_value is not None and account_obj is None:
            return Response(
                {"Account": ["Account not found for user."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Resolve category by id or name (scoped to user)
        category_obj = None
        if category_value is not None:
            try:
                category_obj = Category.objects.get(
                    id=int(category_value), user=request.user
                )
            except Exception:
                category_obj = Category.objects.filter(
                    name=str(category_value), user=request.user
                ).first()

        try:
            print(
                "[ExpensePOST] Resolved Category",
                {
                    "provided": category_value is not None,
                    "found": bool(category_obj),
                    "id": getattr(category_obj, "id", None),
                    "name": getattr(category_obj, "name", None),
                },
            )
        except Exception:
            pass

        # If a category was provided but couldn't be resolved, return a clear error
        if category_value is not None and category_obj is None:
            return Response(
                {"Category": ["Category not found for user."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = {
            **incoming,
            "user": request.user.id,
            "account_name": getattr(account_obj, "id", None),
            "category": getattr(category_obj, "id", None),
        }
        logger.debug(f"Modified data: {payload}")
        try:
            print(
                "[ExpensePOST] Payload",
                {k: (v if k != "details" else "<details>") for k, v in payload.items()},
            )
        except Exception:
            pass

        serializer = ExpenseSerializer(data=payload)
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


class ReceiptOCRCreateExpenseView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Upload a receipt and create an expense",
        operation_description=(
            "Upload a receipt image or PDF. The server runs OCR to extract merchant, date,"
            " and total, then creates an expense. Provide account_id and optionally category_id."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "file": openapi.Schema(
                    type=openapi.TYPE_FILE, description="Receipt file"
                ),
                "account_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="CardAccount ID",
                    format="int32",
                ),
                "category_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Category ID", format="int32"
                ),
            },
            required=["file", "account_id"],
        ),
        responses={
            201: openapi.Response("Created"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        # Debug prints to troubleshoot CSRF/auth/file upload
        try:
            print(
                "[ReceiptOCR] POST invoked",
                {
                    "is_authenticated": getattr(
                        request.user, "is_authenticated", False
                    ),
                    "user": getattr(request.user, "id", None),
                    "method": request.method,
                    "content_type": request.META.get("CONTENT_TYPE"),
                    "has_x_csrf_header": bool(request.headers.get("X-CSRFToken")),
                    "cookie_csrf_present": bool(request.COOKIES.get("csrftoken")),
                },
            )
        except Exception:
            pass

        uploaded = request.FILES.get("file")
        account_id = request.data.get("account_id")
        category_id = request.data.get("category_id")

        if not uploaded or not account_id:
            try:
                print(
                    "[ReceiptOCR] Missing required fields",
                    {
                        "has_file": bool(uploaded),
                        "account_id": account_id,
                        "data_keys": list(getattr(request.data, "keys", lambda: [])()),
                        "files_keys": list(
                            getattr(request.FILES, "keys", lambda: [])()
                        ),
                    },
                )
            except Exception:
                pass
            return Response({"error": "file and account_id are required"}, status=400)

        # Persist uploaded file to a temp path
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

        tmp_path = _save_uploaded_to_temp(uploaded)
        try:
            try:
                print(
                    "[ReceiptOCR] Saved upload to temp",
                    {"tmp_path": tmp_path, "filename": getattr(uploaded, "name", None)},
                )
            except Exception:
                pass
            fields = extract_receipt_fields(tmp_path)
        finally:
            try:
                import os

                os.remove(tmp_path)
            except Exception:
                pass

        # Resolve account and category
        try:
            account = CardAccount.objects.get(id=account_id, user=request.user)
        except CardAccount.DoesNotExist:
            return Response({"error": "Account not found"}, status=400)

        if category_id:
            try:
                category = Category.objects.get(id=category_id, user=request.user)
            except Category.DoesNotExist:
                return Response({"error": "Category not found"}, status=400)
        else:
            category = Category.objects.filter(
                user=request.user, name="Unknown"
            ).first()

        # Build payload for serializer
        description = fields.get("merchant") or "Receipt"
        date_str = fields.get("date")
        total = fields.get("total")
        amount = float(total) if isinstance(total, (int, float)) else None
        if amount is None:
            try:
                print("[ReceiptOCR] Unable to detect total", {"fields": fields})
            except Exception:
                pass
            return Response(
                {"error": "Unable to detect total from receipt"}, status=400
            )

        # Expenses are negative in import pipeline; store negative amount
        amount = -abs(amount)

        payload = {
            "user": request.user.id,
            "amount": amount,
            "date": date_str,
            "description": description,
            "account_name": account.id,
            "category": category.id if category else None,
            "details": {"ocr": fields},
        }

        try:
            print(
                "[ReceiptOCR] Creating Expense",
                {
                    "account": account.id,
                    "category": getattr(category, "id", None),
                    "amount": amount,
                    "date": date_str,
                    "description": description,
                },
            )
        except Exception:
            pass

        serializer = ExpenseSerializer(data=payload)
        if serializer.is_valid():
            instance = serializer.save(user=request.user)
            data = serializer.data
            # Enrich with Account/Category names for frontend convenience
            data["Account"] = account.name
            data["Category"] = category.name if category else None
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Receipt OCR create invalid: {serializer.errors}")
            try:
                print("[ReceiptOCR] Serializer invalid", {"errors": serializer.errors})
            except Exception:
                pass
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
