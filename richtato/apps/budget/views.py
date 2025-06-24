import calendar
from datetime import datetime
from decimal import Decimal

import pytz
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from loguru import logger

from richtato.apps.expense.models import Expense
from richtato.apps.richtato_user.models import Budget, Category
from richtato.utilities.tools import format_currency


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
