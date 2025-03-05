import json
import os
from datetime import datetime

from apps.account.models import Account
from apps.income.models import Income
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from utilities.tools import (
    color_picker,
    format_currency,
    format_date,
    month_mapping,
)


@login_required
def main(request):
    earnings_dates = (
        Income.objects.filter(user=request.user)
        .exclude(date__isnull=True)
        .values_list("date", flat=True)
        .distinct()
    )
    years_list = sorted(set(date.year for date in earnings_dates), reverse=True)
    account_names = Account.objects.filter(user=request.user)
    account_name_list = [account.name for account in account_names]
    entries = Income.objects.filter(user=request.user).order_by("-date")
    return render(
        request,
        "income.html",
        {
            "years": years_list,
            "entries": entries,
            "accounts": account_name_list,
            "today_date": datetime.today().strftime("%Y-%m-%d"),
            "deploy_stage": os.getenv("DEPLOY_STAGE"),
        },
    )


@login_required
def add_entry(request):
    if request.method == "POST":
        # Get the form data
        description = request.POST.get("description")
        amount = request.POST.get("amount")
        date = request.POST.get("balance-date")
        account = request.POST.get("account")

        account_name = Account.objects.get(user=request.user, name=account)
        # Create and save the transaction
        transaction = Income(
            user=request.user,
            account_name=account_name,
            description=description,
            date=date,
            amount=amount,
        )
        transaction.save()
        return HttpResponseRedirect(reverse("income"))
    return HttpResponse("Data Entry Error")


@login_required
def update(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            for transaction_data in data:
                delete_bool = transaction_data.get("delete")
                transaction_id = transaction_data.get("id")
                account_name = transaction_data.get("name")
                date = transaction_data.get("date")
                amount = transaction_data.get("amount")
                amount = float(amount.replace("$", "").replace(",", ""))

                if delete_bool:
                    Income.objects.get(id=transaction_id).delete()
                    continue

                Income.objects.update_or_create(
                    user=request.user,
                    id=transaction_id,
                    defaults={
                        "date": date,
                        "amount": amount,
                    },
                )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def get_plot_data(request):
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

    all_incomes = Income.objects.filter(user=request.user, date__year=year)
    datasets = []

    if group_by == "account":
        group_items = Account.objects.filter(user=request.user)
        item_key = "account_name"
    elif group_by == "description":
        group_items = (
            Income.objects.filter(user=request.user, date__year=year)
            .values_list("description", flat=True)
            .distinct()
        )
        item_key = "description"
    else:
        return JsonResponse({"error": "Invalid group_by value"}, status=400)

    for index, item in enumerate(group_items):
        annual_total = []

        for month in range(1, 13):
            monthly_total = all_incomes.filter(
                **{item_key: item, "date__month": month}
            ).aggregate(Sum("amount"))["amount__sum"]
            annual_total.append(float(monthly_total or 0))

        background_color, border_color = color_picker(index)
        if type(item) == str:
            label = item
        else:
            label = item.name
        datasets.append(
            {
                "label": label,
                "data": annual_total,
                "backgroundColor": background_color,
                "borderColor": border_color,
                "borderWidth": 1,
            }
        )

    return JsonResponse({"labels": month_list, "datasets": datasets})


@login_required
def get_table_data(request):
    year = request.GET.get("year", None)
    month = month_mapping(request.GET.get("month", None))
    account = request.GET.get("label", None)

    table_data = []
    if year and month and account:
        incomes = Income.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month,
            account_name__name=account,
        )
        for income in incomes:
            table_data.append(
                {
                    "id": income.id,
                    "date": format_date(income.date),
                    "description": income.description,
                    "amount": format_currency(income.amount),
                }
            )

    return JsonResponse(table_data, safe=False)
