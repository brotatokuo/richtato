"""
Expense views - Thin HTTP wrappers delegating to service layer.

Following clean architecture: Views handle only HTTP concerns.
Business logic is in services, database access is in repositories.
"""

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

from artificial_intelligence.ai import OpenAI
from .models import Expense
from .repositories import (
    CardAccountRepository,
    CategoryRepository,
    ExpenseRepository,
)
from .serializers import ExpenseSerializer
from .services import ExpenseImportService, ExpenseService


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class ExpenseAPIView(BaseAPIView):
    """ViewSet for managing expenses - THIN WRAPPER."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.expense_repo = ExpenseRepository()
        self.account_repo = CardAccountRepository()
        self.category_repo = CategoryRepository()
        # Inject services with dependencies
        self.expense_service = ExpenseService(
            self.expense_repo, self.account_repo, self.category_repo
        )

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
        """Get expense entries - delegates to service layer."""
        from datetime import datetime as _dt

        # Extract parameters
        limit_param = request.GET.get("limit", None)
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        try:
            limit = int(limit_param) if limit_param is not None else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        # Parse dates
        start_date = None
        end_date = None
        try:
            if start_date_str:
                start_date = _dt.strptime(start_date_str, "%Y-%m-%d").date()
            if end_date_str:
                end_date = _dt.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
            )

        # Delegate to service
        data = self.expense_service.get_user_expenses_formatted(
            request.user, limit, start_date, end_date
        )
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
        """Create a new expense - delegates to service layer."""
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

        if not self.account_repo.get_by_id(account_id, request.user):
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
            if not self.category_repo.get_by_id(category_id, request.user):
                return Response(
                    {"category": ["Category not found for user."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Normalize payload for serializer
        modified_data["account_name"] = account_id
        if category_id is not None:
            modified_data["category"] = category_id

        logger.debug(f"Modified data: {modified_data}")

        serializer = ExpenseSerializer(data=modified_data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        """Update an existing expense - delegates to service layer."""
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
        """Delete an existing expense - delegates to service layer."""
        logger.debug(f"DELETE request for expense with pk: {pk}")
        expense = get_object_or_404(Expense, pk=pk, user=request.user)

        expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExpenseGraphAPIView(APIView):
    """Get expense graph data - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.expense_repo = ExpenseRepository()
        self.account_repo = CardAccountRepository()
        self.category_repo = CategoryRepository()
        # Inject service with dependencies
        self.expense_service = ExpenseService(
            self.expense_repo, self.account_repo, self.category_repo
        )

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
        """Get graph data - delegates to service layer."""
        date_range = request.query_params.get("range", "all")
        logger.debug(f"Date range: {date_range}")

        if date_range == "all":
            chart_data = self.expense_service.get_graph_data_by_month(request.user)
        elif date_range == "30d":
            logger.debug("Getting data for the last 30 days")
            chart_data = self.expense_service.get_graph_data_by_day(request.user)
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
    """Get field choices for expense creation - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.expense_repo = ExpenseRepository()
        self.account_repo = CardAccountRepository()
        self.category_repo = CategoryRepository()
        # Inject service with dependencies
        self.expense_service = ExpenseService(
            self.expense_repo, self.account_repo, self.category_repo
        )

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
        """Get field choices - delegates to service layer."""
        data = self.expense_service.get_field_choices(request.user)
        return Response(data)


@method_decorator(csrf_exempt, name="dispatch")
class CategorizeTransactionView(APIView):
    """Categorize transaction using AI - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.expense_repo = ExpenseRepository()
        self.account_repo = CardAccountRepository()
        self.category_repo = CategoryRepository()
        # Inject service with dependencies
        self.import_service = ExpenseImportService(
            self.expense_repo, self.account_repo, self.category_repo
        )

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
        """Categorize a transaction - delegates to service layer."""
        description = request.data.get("description")
        if not description:
            return Response({"error": "Description is required."}, status=400)

        # Delegate to service (passing AI service as dependency)
        ai_service = OpenAI()
        category_id, error = self.import_service.categorize_transaction(
            request.user, description, ai_service
        )

        if error:
            return Response({"error": error}, status=400)

        logger.debug(f"Categorized as category_id={category_id}")
        return Response({"category": category_id})


class ImportStatementsView(APIView):
    """Import bank statements - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.expense_repo = ExpenseRepository()
        self.account_repo = CardAccountRepository()
        self.category_repo = CategoryRepository()
        # Inject service with dependencies
        self.import_service = ExpenseImportService(
            self.expense_repo, self.account_repo, self.category_repo
        )

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
        """Import statements and categorize transactions - delegates to service layer."""

        def ensure_list(obj):
            if obj is None:
                return []
            if isinstance(obj, list):
                return obj
            return [obj]

        # Get files and card accounts from request
        files = ensure_list(request.FILES.getlist("files"))
        card_accounts = ensure_list(request.data.getlist("card_accounts"))
        logger.debug(f"Files: {files}")
        logger.debug(f"Card Accounts: {card_accounts}")

        # Process files
        for file, card_account in zip(files, card_accounts):
            card = self.account_repo.get_by_id(int(card_account), request.user)
            if not card:
                continue

            logger.debug(f"Card: {card}")
            name_lower = (getattr(file, "name", "") or "").lower()

            # Only support CSV/XLSX files
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

            # Delegate to import service
            (
                success_count,
                error_count,
                errors,
            ) = self.import_service.import_from_dataframe(
                card_statement.formatted_df, request.user
            )

            logger.debug(
                f"Import completed: {success_count} success, {error_count} errors"
            )

        return Response({"message": "File processed successfully."})
