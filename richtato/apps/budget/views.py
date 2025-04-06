import calendar
from datetime import datetime
from decimal import Decimal

import pytz
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from loguru import logger

from richtato.apps.expense.models import Expense
from richtato.apps.richtato_user.models import Category
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

    print(years_list, months_list)
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
    pst = pytz.timezone("US/Pacific")
    year = request.GET.get("year", datetime.now(pst).year)
    month_abbr = request.GET.get("month", datetime.now(pst).strftime("%b"))
    month_map = {
        month: index for index, month in enumerate(calendar.month_abbr) if month
    }
    month = month_map.get(month_abbr)

    logger.debug(f"Year: {year}, Month: {month}")

    # Get budgets and expenses in one go
    budget_list = Category.objects.filter(user=user).values("name", "budget")
    budget_expenses = []

    for budget in budget_list:
        total_expense = Expense.objects.filter(
            user=user,
            category__name=budget["name"],
            date__year=year,
            date__month=month,
        ).aggregate(total_amount=Coalesce(Sum("amount"), Decimal(0)))["total_amount"]

        percent_budget = (
            round(total_expense / budget["budget"] * 100) if budget["budget"] else 0
        )
        budget_expenses.append(
            {
                "category_name": budget["name"],
                "budget": budget["budget"],
                "expense": total_expense,
                "difference": total_expense - budget["budget"],
                "percent_budget": percent_budget,
            }
        )

    # Sort and get top 3 budget categories by percent spent
    budget_rankings = sorted(
        budget_expenses, key=lambda x: x["percent_budget"], reverse=True
    )

    if count:
        budget_rankings = budget_rankings[: int(count)]

    # Prepare the category data for the response
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

    return JsonResponse({"category_rankings": category_data})
    return JsonResponse({"category_rankings": category_data})
    return JsonResponse({"category_rankings": category_data})
