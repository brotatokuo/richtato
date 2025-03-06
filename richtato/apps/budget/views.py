import calendar
import os

import pandas as pd
from apps.expense.models import Expense
from apps.richtato_user.models import Category
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from utilities.tools import convert_currency_to_str_float, month_mapping


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
    months_list = sorted(
        list(set([(date.year, date.month) for date in expense_dates])), reverse=True
    )
    months_list = [calendar.month_abbr[month[1]] for month in months_list]
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
            "deploy_stage": os.getenv("DEPLOY_STAGE"),
        },
    )


@login_required
def get_plot_data(request, year, month):
    month_number = month_mapping(month)
    expense_for_month = (
        Expense.objects.filter(
            user=request.user, date__year=year, date__month=month_number
        )
        .values("category__name")
        .annotate(total_amount=Sum("amount"))
    )

    categories = Category.objects.filter(user=request.user).values(
        "name", "budget", "color"
    )

    datasets = []
    labels = []

    for i, category in enumerate(categories):
        category_name = category["name"]
        budget = category["budget"]
        color = category["color"]

        expense = next(
            (
                exp
                for exp in expense_for_month
                if exp["category__name"] == category_name
            ),
            None,
        )
        total_amount = expense["total_amount"] if expense else 0
        budget_percent = round(total_amount * 100 / budget) if budget else 0

        labels.append(category_name)
        budget_placeholder = [0] * len(categories)
        budget_placeholder[i] = budget_percent
        datasets.append(
            {
                "label": category_name,
                "backgroundColor": color,
                "borderColor": color,
                "borderWidth": 1,
                "data": budget_placeholder,
            }
        )

    return JsonResponse({"labels": labels, "datasets": datasets})


def get_table_data(request):
    year = request.GET.get("year")
    month = month_mapping(request.GET.get("month"))
    category = request.GET.get("label")

    table_data = []
    expenses = Expense.objects.filter(
        user=request.user, date__year=year, date__month=month, category__name=category
    )
    for expense in expenses:
        table_data.append(
            {
                "id": expense.id,
                "date": expense.date,
                "description": expense.description,
                "amount": convert_currency_to_str_float(expense.amount),
            }
        )

    return JsonResponse(table_data, safe=False)


@login_required
def get_budget_data_json(request):
    print("Get Budget Table Data")
    year = request.GET.get("year")
    label = request.GET.get("label")
    month = request.GET.get("month")

    print("Year: ", year, "Label: ", label, "Month: ", month)
    # df = get_transaction_data(request.user, context="Spendings")
    df = None
    # Filter data by year, label (description), and month
    df_filtered = df[df["Year"] == int(year)]
    df_filtered = df_filtered[df_filtered["Category"] == label]
    df_filtered = df_filtered[df_filtered["Month"] == int(month)]

    # Print filtered data for debugging
    print("Filtered Spendings Data: ", df_filtered)

    # Convert Date to 'YYYY-MM-DD' format and Balance to currency format
    df_filtered["Date"] = pd.to_datetime(df_filtered["Date"]).dt.strftime("%Y-%m-%d")
    df_filtered["Amount"] = df_filtered["Amount"].apply(
        lambda x: f"${x:,.2f}"
    )  # Format to 2 decimal places with currency symbol

    # Rename columns for JSON response
    df_filtered = df_filtered.rename(
        columns={"Account Name": "Name", "Date": "Date", "id": "Id"}
    )

    json_data = df_filtered[["Id", "Date", "Name", "Description", "Amount"]].to_dict(
        orient="records"
    )
    return JsonResponse(json_data, safe=False)


def plot_category_monthly_data(request):
    print("Plot Category Monthly Data")
    print("Request: ", request)

    # Check if the request method is GET
    if request.method == "GET":
        year = request.GET.get("year")
        category = request.GET.get("category")
        # Get color from the category
        category_obj = Category.objects.get(user=request.user, name=category)
        color = category_obj.color
        print("Category Color: ", color)
        print("Plot Category Monthly Data", year, category)

        # Get the data
        df = get_category_table_data(request, year, category)

        # Group by Month and sum the Amount
        df_grouped = df.groupby(["Month"])["Amount"].sum().reset_index()

        # Prepare the JSON response for Chart.js
        json_data = {
            "labels": [
                calendar.month_abbr[i] for i in range(1, 13)
            ],  # Abbreviated month names
            "datasets": [
                {
                    "label": category,  # You might want to add the category label for the dataset
                    "data": df_grouped["Amount"]
                    .round(2)
                    .tolist(),  # Monthly summed amounts
                    "backgroundColor": color,
                    "borderColor": color,
                    "borderWidth": 10,
                }
            ],
        }

        print("Filtered Data Grouped: ", json_data)
        return JsonResponse(json_data, safe=False)

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def get_category_table_data(request, year, category):
    # df = get_transaction_data(request.user, context="Spendings")
    df = None

    # Correct filtering with parentheses
    df_filtered = df[
        (df["Year"] == int(year)) & (df["Category"] == category)
    ]  # This needs to be exported to the table data function

    return df_filtered
