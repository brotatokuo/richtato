import calendar
from datetime import datetime
from decimal import Decimal

import pytz
from apps.budget.models import Budget
from apps.budget.serializers import BudgetSerializer
from apps.expense.models import Expense
from apps.richtato_user.models import Category
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
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
from utilities.tools import format_currency

# Template-based views removed - API-only backend


def calculate_budget_diff(diff: float):
    if diff <= 0:
        return f"{format_currency(abs(diff))} left"
    else:
        return f"{format_currency(abs(diff))} over"


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
    count = request.GET.get("count", None)

    user = request.user
    utc = pytz.timezone("UTC")
    year = int(request.GET.get("year", datetime.now(utc).year))
    month_abbr = request.GET.get("month", datetime.now(utc).strftime("%b"))

    month_map = {
        month: index for index, month in enumerate(calendar.month_abbr) if month
    }
    month = month_map.get(month_abbr)
    if not month:
        return JsonResponse({"error": "Invalid month"}, status=400)

    logger.debug(f"Year: {year}, Month: {month}")

    # Target month date range
    start_of_month = datetime(year, month, 1, tzinfo=utc)
    last_day = calendar.monthrange(year, month)[1]
    end_of_month = datetime(year, month, last_day, 23, 59, 59, tzinfo=utc)

    # Get budgets active during the month
    logger.debug(f"Start of month: {start_of_month}, End of month: {end_of_month}")
    budgets = (
        Budget.objects.filter(
            user=user,
            start_date__lte=end_of_month,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=start_of_month))
        .select_related("category")
    )
    logger.debug(f"Budgets found: {budgets.count()}")
    logger.debug(f"Budgets: {budgets}")
    budget_expenses = []
    for budget in budgets:
        total_expense = Expense.objects.filter(
            user=user,
            category=budget.category,
            date__gte=start_of_month,
            date__lt=end_of_month,
        ).aggregate(total=Coalesce(Sum("amount"), Decimal(0)))["total"]

        percent_budget = (
            round(total_expense / budget.amount * 100) if budget.amount else 0
        )

        budget_expenses.append(
            {
                "category_name": budget.category.name,
                "budget": budget.amount,
                "expense": total_expense,
                "difference": total_expense - budget.amount,
                "percent_budget": percent_budget,
            }
        )

    # Sort by budget % used
    budget_rankings = sorted(
        budget_expenses, key=lambda x: x["percent_budget"], reverse=True
    )

    if count:
        budget_rankings = budget_rankings[: int(count)]

    category_data = [
        {
            "name": ranking["category_name"],
            "budget": ranking["budget"],
            "spent": ranking["expense"],
            "percent": ranking["percent_budget"],
            "message": f"{calculate_budget_diff(ranking['difference'])} ({ranking['percent_budget']}%)",
        }
        for ranking in budget_rankings
    ]
    logger.debug(f"Category Data: {category_data}")
    return JsonResponse({"category_rankings": category_data})


class BudgetAPIView(BaseAPIView):
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
        """
        Get budget entries for the user, or a specific budget if pk is provided.
        """
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

        budgets = (
            Budget.objects.filter(user=request.user)
            .select_related("category")
            .order_by("-start_date")
            .values(
                "id",
                "start_date",
                "end_date",
                "amount",
                category_name=F("category__name"),
            )
        )

        if limit:
            budgets = budgets[:limit]

        rows = [
            {
                "id": b["id"],
                "category": b["category_name"],
                "amount": b["amount"],
                "start_date": b["start_date"],
                "end_date": b["end_date"],
            }
            for b in budgets
        ]

        return Response(
            {
                "columns": [
                    {"field": "id", "title": "ID"},
                    {"field": "category", "title": "Category"},
                    {"field": "amount", "title": "Amount"},
                    {"field": "start_date", "title": "Start Date"},
                    {"field": "end_date", "title": "End Date"},
                ],
                "rows": rows,
            }
        )

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
                    description="End date",
                ),
            },
            required=["category", "amount", "start_date", "end_date"],
        ),
        responses={
            201: openapi.Response("Created"),
            400: openapi.Response("Bad Request"),
        },
    )
    def post(self, request):
        """
        Create a new Budget entry.
        """
        modified_data = request.data.copy()
        modified_data["user"] = request.user.id
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
        """
        Update an existing Budget entry.
        """
        logger.debug(f"PATCH data: {request.data}")
        reversed_data = self.apply_fieldmap(request.data)
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
        """
        Delete an existing Budget entry.
        """
        logger.debug(f"DELETE Budget ID: {pk}")
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
        budget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BudgetFieldChoicesView(APIView):
    permission_classes = [IsAuthenticated]

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
        """
        Get field choices for the Budget model.
        """
        category_choices = Category.objects.filter(user=request.user)
        data = {
            "category": [
                {"value": cat.id, "label": cat.name} for cat in category_choices
            ],
        }
        return Response(data)
