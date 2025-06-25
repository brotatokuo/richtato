import calendar
from datetime import datetime
from decimal import Decimal

import pytz
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from loguru import logger
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from richtato.apps.budget.models import Budget
from richtato.apps.budget.serializers import BudgetSerializer
from richtato.apps.expense.models import Expense
from richtato.apps.richtato_user.models import Category
from richtato.utilities.tools import format_currency
from richtato.views import BaseAPIView


@login_required
def main(request) -> HttpResponse:
    """
    Budget view that renders the budget.html template
    """
    expense_dates = (
        Expense.objects.filter(user=request.user)
        .exclude(date__isnull=True)
        .values_list("date", flat=True)
        .distinct()
    )
    years_list = sorted(list(set([date.year for date in expense_dates])), reverse=True)
    unique_month_nums = sorted({date.month for date in expense_dates}, reverse=True)
    months_list = [calendar.month_abbr[month] for month in unique_month_nums]

    category_list = sorted(
        list(Category.objects.filter(user=request.user).values_list("name", flat=True))
    )

    return render(
        request,
        "budget.html",
        {
            "years": years_list,
            "months": months_list,
            "categories": category_list,
        },
    )


def calculate_budget_diff(diff: float):
    if diff <= 0:
        return f"{format_currency(abs(diff))} left"
    else:
        return f"{format_currency(abs(diff))} over"


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
            "budget": format_currency(ranking["budget"]),
            "spent": format_currency(ranking["expense"]),
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

    def get(self, request):
        """
        Get budget entries for the user.
        """
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
                "amount": format_currency(b["amount"]),
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

    def delete(self, request, pk):
        """
        Delete an existing Budget entry.
        """
        logger.debug(f"DELETE Budget ID: {pk}")
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
        budget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BudgetFieldChoicesView(APIView):
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
