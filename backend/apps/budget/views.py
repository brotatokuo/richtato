import calendar
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

import pytz
from apps.budget.models import Budget
from apps.budget.serializers import BudgetSerializer
from apps.expense.models import Expense
from apps.richtato_user.models import Category
from django.contrib.auth.decorators import login_required
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
        """
        Create a new Budget entry.
        """
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
        """
        Update an existing Budget entry.
        """
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


@login_required
def budget_progress(request):
    """Function view: budget progress over a date range.

    Accepts start_date/end_date (YYYY-MM-DD) or year/month. Defaults to current month.
    """
    today = date.today()
    year_param = request.GET.get("year")
    month_param = request.GET.get("month")
    start_date_param = request.GET.get("start_date")
    end_date_param = request.GET.get("end_date")

    start_date: date | None = None
    end_date: date | None = None
    year = today.year
    month = today.month

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

        month_val: int | None = None
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

    assert start_date is not None and end_date is not None
    if end_date < start_date:
        return JsonResponse(
            {"error": "end_date must be on/after start_date"}, status=400
        )

    budgets = (
        Budget.objects.filter(user=request.user, start_date__lte=end_date)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=start_date))
        .select_related("category")
    )

    results = []
    for b in budgets:
        total_spent = (
            Expense.objects.filter(
                user=request.user,
                category=b.category,
                date__gte=start_date,
                date__lte=end_date,
            ).aggregate(total=Coalesce(Sum("amount"), Decimal(0)))
        )["total"]
        budget_amount = b.amount or Decimal(0)
        percentage = (
            int(round((total_spent / budget_amount) * 100)) if budget_amount > 0 else 0
        )
        # Round monetary fields to 2 decimals
        budget_amount_q = budget_amount.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_spent_q = total_spent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        remaining_q = (budget_amount - total_spent).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        results.append(
            {
                "category": b.category.name,
                "budget": float(budget_amount_q),
                "spent": float(total_spent_q),
                "percentage": percentage,
                "remaining": float(remaining_q),
                "year": year,
                "month": month,
            }
        )

    return JsonResponse(
        {
            "budgets": results,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
    )


class BudgetDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Delegate to function-based view for shared logic
        return budget_progress(request)
