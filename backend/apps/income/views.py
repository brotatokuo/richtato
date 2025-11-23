"""
Income views - Thin HTTP wrappers delegating to service layer.

Following clean architecture: Views handle only HTTP concerns.
Business logic is in services, database access is in repositories.
"""

from django.shortcuts import get_object_or_404
from loguru import logger
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from richtato.views import BaseAPIView

from apps.account.repositories import AccountRepository
from .models import Income
from .repositories import IncomeRepository
from .serializers import IncomeSerializer
from .services import IncomeService


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
class IncomeAPIView(BaseAPIView):
    """ViewSet for managing income - THIN WRAPPER."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.income_repo = IncomeRepository()
        self.account_repo = AccountRepository()
        # Inject service with dependencies
        self.income_service = IncomeService(self.income_repo, self.account_repo)

    @property
    def field_remap(self):
        return {}

    def get(self, request):
        """Get income entries for user - delegates to service layer."""
        from datetime import datetime as _dt

        # Extract query parameters
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
        data = self.income_service.get_user_income_formatted(
            request.user, limit, start_date, end_date
        )
        return Response(data)

    def post(self, request):
        """Create a new income entry - delegates to service layer."""
        logger.debug(f"Request data: {request.data}")

        # Enforce ID usage
        if "Account" in request.data and not isinstance(
            request.data.get("Account"), int
        ):
            return Response(
                {
                    "error": "Deprecated fields. Use integer IDs only.",
                    "details": {"Account": "Account ID (for account_name)"},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate account ownership
        account_id = request.data.get("Account")
        if account_id is not None:
            try:
                account_id = int(account_id)
            except (TypeError, ValueError):
                return Response(
                    {"Account": ["Must be an integer ID."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not self.account_repo.get_by_id(account_id, request.user):
                return Response(
                    {"Account": ["Account not found for user."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = IncomeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Update an existing income entry - delegates to service layer."""
        logger.debug(f"PATCH request data: {request.data}")

        if "Account" in request.data and not isinstance(
            request.data.get("Account"), int
        ):
            return Response(
                {
                    "error": "Deprecated fields. Use integer IDs only.",
                    "details": {"Account": "Account ID (for account_name)"},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate account ownership if Account is being updated
        account_id = request.data.get("Account")
        if account_id is not None:
            try:
                account_id = int(account_id)
            except (TypeError, ValueError):
                return Response(
                    {"Account": ["Must be an integer ID."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not self.account_repo.get_by_id(account_id, request.user):
                return Response(
                    {"Account": ["Account not found for user."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        reversed_data = self.apply_fieldmap(request.data)
        income = get_object_or_404(Income, pk=pk, user=request.user)

        serializer = IncomeSerializer(income, data=reversed_data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete an existing income entry - delegates to service layer."""
        logger.debug(f"DELETE request for Income with pk: {pk}")
        income = get_object_or_404(Income, pk=pk, user=request.user)

        income.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IncomeGraphAPIView(APIView):
    """Get income graph data - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.income_repo = IncomeRepository()
        self.account_repo = AccountRepository()
        # Inject service with dependencies
        self.income_service = IncomeService(self.income_repo, self.account_repo)

    def get(self, request):
        """Get graph data - delegates to service layer."""
        date_range = request.query_params.get("range", "all")
        logger.debug(f"Date range: {date_range}")

        if date_range == "all":
            chart_data = self.income_service.get_graph_data_by_month(request.user)
        elif date_range == "30d":
            logger.debug("Getting data for the last 30 days")
            chart_data = self.income_service.get_graph_data_by_day(request.user)
        else:
            return Response({"error": "Invalid range. Use '30d' or 'all'."}, status=400)

        return Response(
            {
                "labels": chart_data["labels"],
                "datasets": [
                    {
                        "label": "Income",
                        "data": chart_data["values"],
                        "backgroundColor": "rgba(152, 204, 44, 0.2)",
                        "borderColor": "rgba(152, 204, 44, 1)",
                        "borderWidth": 1,
                    }
                ],
            }
        )


class IncomeFieldChoicesView(APIView):
    """Get field choices for income creation - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.income_repo = IncomeRepository()
        self.account_repo = AccountRepository()
        # Inject service with dependencies
        self.income_service = IncomeService(self.income_repo, self.account_repo)

    def get(self, request):
        """Get field choices - delegates to service layer."""
        data = self.income_service.get_field_choices(request.user)
        return Response(data)
