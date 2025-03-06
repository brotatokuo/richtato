import json
import os
from datetime import datetime

import pytz
from apps.expense.models import Expense, ExpenseDB
from apps.income.models import Income
from apps.richtato_user.models import CardAccount, Category
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from google_gemini.ai import AI
from graph.chart_theme import ChartTheme
from utilities.tools import (
    color_picker,
    convert_currency_to_str_float,
    format_date,
    month_mapping,
)

pst = pytz.timezone("US/Pacific")


@login_required
def main(request):
    spending_dates = (
        Expense.objects.filter(user=request.user)
        .exclude(date__isnull=True)
        .values_list("date", flat=True)
        .distinct()
    )
    years_list = sorted(set(date.year for date in spending_dates), reverse=True)
    transaction_accounts = (
        CardAccount.objects.filter(user=request.user)
        .values_list("name", flat=True)
        .distinct()
    )
    category_list = [""] + list(
        Category.objects.filter(user=request.user).values_list("name", flat=True)
    )

    return render(
        request,
        "expense.html",
        {
            "years": years_list,
            "transaction_accounts": transaction_accounts,
            "category_list": category_list,
            "today_date": datetime.now(pst).strftime("%Y-%m-%d"),
            "deploy_stage": os.getenv("DEPLOY_STAGE"),
        },
    )


@login_required
def add_entry(request):
    if request.method == "POST":
        description = request.POST.get("description")
        amount = request.POST.get("amount")
        date = request.POST.get("balance-date")
        category = request.POST.get("category")
        account = request.POST.get("account")

        ExpenseDB(request.user).add(account, description, category, date, amount)

        return HttpResponseRedirect(reverse("expense"))
    return HttpResponse("Data Entry Error")


@login_required
def update(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    try:
        data = json.loads(request.body.decode("utf-8"))

        for transaction_data in data:
            delete_bool = transaction_data.get("delete")
            transaction_id = transaction_data.get("id")
            if delete_bool:
                ExpenseDB(request.user).delete(transaction_id)
                continue
            else:
                account_name = transaction_data.get("card")
                description = transaction_data.get("description")
                date = transaction_data.get("date")
                amount = (
                    transaction_data.get("amount", "").replace("$", "").replace(",", "")
                )
                category_name = transaction_data.get("category", None)

                ExpenseDB(request.user).update(
                    transaction_id,
                    date,
                    description,
                    amount,
                    category_name,
                    account_name,
                )

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def get_plot_data(request) -> JsonResponse:
    year = request.GET.get("year")
    group_by = request.GET.get("group_by")

    month_list = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    datasets = []
    all_expenses = Expense.objects.filter(user=request.user, date__year=year)

    if group_by == "card":
        group_items = CardAccount.objects.filter(user=request.user)
        item_key = "account_name"
    elif group_by == "category":
        group_items = Category.objects.filter(user=request.user)
        item_key = "category"
    else:
        return JsonResponse({"error": "Invalid group_by value"}, status=400)

    color_theme = ChartTheme().get_theme("default")
    for index, item in enumerate(group_items):
        annual_total = []

        for month in range(1, 13):
            monthly_total = all_expenses.filter(
                **{item_key: item, "date__month": month}
            ).aggregate(Sum("amount"))["amount__sum"]
            annual_total.append(float(monthly_total or 0))

        # background_color, border_color = color_picker(index)
        color = color_theme[index]
        datasets.append(
            {
                "label": item.name,
                "data": annual_total,
                "backgroundColor": color,
                "borderColor": color,
                "borderWidth": 1,
            }
        )

    return JsonResponse({"labels": month_list, "datasets": datasets})


def get_table_data(request) -> JsonResponse:
    year = request.GET.get("year", None)
    month = month_mapping(request.GET.get("month", None))
    print("Month:", month)
    account = request.GET.get("label", None)

    table_data = []
    if year and month and account:
        expenses = Expense.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month,
            account_name__name=account,
        )
        for expense in expenses:
            table_data.append(
                {
                    "id": expense.id,
                    "date": format_date(expense.date),
                    "card": expense.account_name.name,
                    "description": expense.description,
                    "amount": convert_currency_to_str_float(expense.amount),
                    "category": expense.category.name,
                }
            )
    print(table_data)
    return JsonResponse(table_data, safe=False)


def guess_category(request):
    """
    Guess the category of an expense based on the description.
    """
    description = request.GET.get("description", "").lower().strip()

    if not description:
        return JsonResponse({"category": ""})

    # Try to find a category that matches the description
    user_categories = Category.objects.filter(user=request.user)

    for category in user_categories:
        if description in category.keywords.lower():
            return JsonResponse({"category": category.name})

    # Use AI categorization if no match is found
    try:
        category_str = AI().categorize_transaction(request.user, description)
        return JsonResponse({"category": category_str})
    except Exception:
        return JsonResponse({"category": ""})


def get_monthly_diff(request):
    """
    Get the monthly diff between income and expenses.
    """
    year = request.GET.get("year") or 2024

    month_list = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    datasets = []
    all_expenses = Expense.objects.filter(user=request.user, date__year=year)
    all_incomes = Income.objects.filter(user=request.user, date__year=year)

    monthly_diffs = []

    for month in range(1, 13):
        # Filter expenses and incomes for the specific month and calculate totals
        monthly_expense = (
            all_expenses.filter(date__month=month).aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        monthly_income = (
            all_incomes.filter(date__month=month).aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        monthly_diff = round(float(monthly_income) - float(monthly_expense))

        # Append the difference to the monthly_diffs list
        monthly_diffs.append(monthly_diff)

    # Create the dataset for the chart
    background_color, border_color = color_picker(
        0
    )  # Assuming this function returns the correct colors
    datasets.append(
        {
            "label": "Monthly Diff",
            "data": monthly_diffs,
            "backgroundColor": background_color,
            "borderColor": border_color,
            "borderWidth": 1,
        }
    )

    # Return the JSON response
    return JsonResponse({"labels": month_list, "datasets": datasets})


def get_full_table_data(request):
    year = request.GET.get("year")
    month = request.GET.get("month")

    table_data = []
    expenses = Expense.objects.filter(
        user=request.user, date__year=year, date__month=month
    )
    for expense in expenses:
        table_data.append(
            {
                "id": expense.id,
                "date": format_date(expense.date),
                "description": expense.description,
                "amount": convert_currency_to_str_float(expense.amount),
                "category": expense.category.name,
            }
        )
    return JsonResponse(table_data, safe=False)
