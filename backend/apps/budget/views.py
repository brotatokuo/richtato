"""
Budget views - Thin HTTP wrappers delegating to service layer.

Following clean architecture: Views handle only HTTP concerns.
Business logic is in services, database access is in repositories.
"""

import calendar
from datetime import date, datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from loguru import logger
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from richtato.views import BaseAPIView

from .models import Budget
from .repositories import BudgetRepository, CategoryRepository, ExpenseRepository
from .serializers import BudgetSerializer
from .services import BudgetService


@swagger_auto_schema(
    operation_summary="Get budget rankings",
    operation_description="Get budget rankings showing spending vs budget for each category",
    manual_parameters=[
        openapi.Parameter(
            "count",
            openapi.IN_QUERY,
            description="Number of categories to return",
            type=openapi.TYPE_INTEGER,
        ),
        openapi.Parameter(
            "year",
            openapi.IN_QUERY,
            description="Year for budget calculations",
            type=openapi.TYPE_INTEGER,
        ),
    ],
    responses={
        200: openapi.Response(
            "Success", examples={"application/json": {"category_rankings": []}}
        )
    },
)
def get_budget_rankings(request):
    """Get budget rankings - delegates to service layer."""
    # Extract parameters
    count_param = request.GET.get("count", None)
    count = int(count_param) if count_param else None

    utc = pytz.timezone("UTC")
    year = int(request.GET.get("year", datetime.now(utc).year))
    month_abbr = request.GET.get("month", datetime.now(utc).strftime("%b"))

    # Parse month
    month_map = {
        month: index for index, month in enumerate(calendar.month_abbr) if month
    }
    month = month_map.get(month_abbr)
    if not month:
        return JsonResponse({"error": "Invalid month"}, status=400)

    logger.debug(f"Year: {year}, Month: {month}")

    # Inject dependencies and delegate to service
    budget_repo = BudgetRepository()
    expense_repo = ExpenseRepository()
    category_repo = CategoryRepository()
    budget_service = BudgetService(budget_repo, expense_repo, category_repo)

    # Delegate to service
    category_data = budget_service.get_budget_rankings(request.user, year, month, count)

    return JsonResponse({"category_rankings": category_data})


class BudgetAPIView(BaseAPIView):
    """ViewSet for managing budgets - THIN WRAPPER."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.budget_repo = BudgetRepository()
        self.expense_repo = ExpenseRepository()
        self.category_repo = CategoryRepository()
        # Inject service with dependencies
        self.budget_service = BudgetService(
            self.budget_repo, self.expense_repo, self.category_repo
        )

    @property
    def field_remap(self):
        return {}

    @swagger_auto_schema(
        operation_summary="Get budget entries",
        operation_description="Retrieve budget entries for the authenticated user or a specific budget by ID",
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
            ),
            404: openapi.Response("Not Found"),
        },
    )
    def get(self, request, pk=None):
        """Get budget entries - delegates to service layer."""
        if pk:
            # Get specific budget
            budget = get_object_or_404(Budget, pk=pk, user=request.user)
            serializer = BudgetSerializer(budget)
            return Response(serializer.data)

        # Get all budgets
        limit_param = request.GET.get("limit", None)
        try:
            limit = int(limit_param) if limit_param else None
        except ValueError:
            return Response({"error": "Invalid limit value"}, status=400)

        # Delegate to service
        data = self.budget_service.get_user_budgets_formatted(request.user, limit)
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Create budget entry",
        operation_description="Create a new budget entry for the authenticated user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "category": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Category ID"
                ),
                "amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Budget amount"
                ),
                "start_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Start date",
                ),
                "end_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="End date (omit for no expiry)",
                ),
            },
            required=["category", "amount", "start_date"],
        ),
        responses={
            201: openapi.Response("Created"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        """Create a new budget - delegates to service layer."""
        modified_data = request.data.copy()
        modified_data["user"] = request.user.id
        if not modified_data.get("end_date"):
            modified_data["end_date"] = None
        logger.debug(f"POST data: {modified_data}")

        serializer = BudgetSerializer(data=modified_data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"POST error: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update budget entry",
        operation_description="Update an existing budget entry",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "category": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Category ID"
                ),
                "amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Budget amount"
                ),
                "start_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="Start date",
                ),
                "end_date": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description="End date",
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
        """Update an existing budget - delegates to service layer."""
        logger.debug(f"PATCH data: {request.data}")
        reversed_data = self.apply_fieldmap(request.data)
        if "end_date" in reversed_data and not reversed_data.get("end_date"):
            reversed_data["end_date"] = None
        budget = get_object_or_404(Budget, pk=pk, user=request.user)

        serializer = BudgetSerializer(budget, data=reversed_data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        logger.error(f"PATCH error: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete budget entry",
        operation_description="Delete an existing budget entry",
        responses={
            204: openapi.Response("No Content"),
            404: openapi.Response("Not Found"),
        },
    )
    def delete(self, request, pk):
        """Delete an existing budget - delegates to service layer."""
        logger.debug(f"DELETE Budget ID: {pk}")
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
        budget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BudgetFieldChoicesView(APIView):
    """Get field choices for budget creation - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject repository dependencies
        self.budget_repo = BudgetRepository()
        self.expense_repo = ExpenseRepository()
        self.category_repo = CategoryRepository()
        # Inject service with dependencies
        self.budget_service = BudgetService(
            self.budget_repo, self.expense_repo, self.category_repo
        )

    @swagger_auto_schema(
        operation_summary="Get budget field choices",
        operation_description="Get available field choices for budget creation/editing",
        responses={
            200: openapi.Response(
                "Success", examples={"application/json": {"category": []}}
            )
        },
    )
    def get(self, request):
        """Get field choices - delegates to service layer."""
        data = self.budget_service.get_field_choices(request.user)
        return Response(data)


@login_required
def budget_progress(request):
    """Get budget progress for a date range - delegates to service layer."""
    today = date.today()
    year_param = request.GET.get("year")
    month_param = request.GET.get("month")
    start_date_param = request.GET.get("start_date")
    end_date_param = request.GET.get("end_date")

    start_date = None
    end_date = None
    year = today.year
    month = today.month

    # Parse date parameters
    if start_date_param or end_date_param:
        try:
            if start_date_param:
                y, m, d = map(int, start_date_param.split("-"))
                start_date = date(y, m, d)
            if end_date_param:
                y2, m2, d2 = map(int, end_date_param.split("-"))
                end_date = date(y2, m2, d2)
        except Exception:
            return JsonResponse({"error": "Invalid start_date or end_date"}, status=400)

        if start_date and not end_date:
            end_date = date(
                start_date.year,
                start_date.month,
                calendar.monthrange(start_date.year, start_date.month)[1],
            )
        if end_date and not start_date:
            start_date = date(end_date.year, end_date.month, 1)

        if start_date:
            year = start_date.year
            month = start_date.month
    else:
        try:
            year = int(year_param) if year_param else today.year
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid year"}, status=400)

        month_val = None
        if month_param:
            try:
                mnum = int(month_param)
                if 1 <= mnum <= 12:
                    month_val = mnum
            except ValueError:
                key = month_param.strip().lower()
                abbr_map = {
                    m.lower(): i for i, m in enumerate(calendar.month_abbr) if m
                }
                name_map = {
                    m.lower(): i for i, m in enumerate(calendar.month_name) if m
                }
                month_val = abbr_map.get(key) or name_map.get(key)
        else:
            month_val = today.month

        if not month_val:
            return JsonResponse({"error": "Invalid month"}, status=400)

        month = month_val
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])

    # Inject dependencies and delegate to service
    budget_repo = BudgetRepository()
    expense_repo = ExpenseRepository()
    category_repo = CategoryRepository()
    budget_service = BudgetService(budget_repo, expense_repo, category_repo)

    # Delegate to service
    result = budget_service.get_budget_progress(
        request.user, year, month, start_date, end_date
    )

    return JsonResponse(result)


class BudgetDashboardView(APIView):
    """Get budget dashboard data - THIN WRAPPER."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get budget dashboard - delegates to function view for shared logic."""
        return budget_progress(request)
