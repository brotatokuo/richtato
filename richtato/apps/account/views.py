import calendar
import json
import pandas as pd
from typing import Any
from datetime import datetime

from django.db.models import F, CharField
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, render
from django.http import JsonResponse
from django.db.models.functions import Cast, TruncYear, TruncMonth, TruncDate, ExtractYear
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.db.models import Sum

from apps.account.models import Account, AccountTransaction
from utilities.tools import color_picker, month_mapping, format_currency, format_date

@login_required
def main(request):
    account_options = Account.objects.filter(user=request.user).values_list("id", "name")
    unique_years = list(
        AccountTransaction.objects.filter(account__user=request.user)
        .annotate(Year=ExtractYear("date"))
        .values_list('Year', flat=True)
        .distinct()
        .order_by('-Year')
    )
    return render(
        request,
        "account.html",
        {
            "networth": format_currency(request.user.networth()),
            "account_options": account_options,
            "years": unique_years,
            "today_date": datetime.today().strftime("%Y-%m-%d"),
        },
    )

@login_required
def add_entry(request):
    if request.method == "POST":
        account = Account.objects.get(id=request.POST.get("account-id"))
        balance = request.POST.get("balance-input")
        date = request.POST.get("balance-date")

        account_history = AccountTransaction(
            account=account,
            amount=balance,
            date=date,
        )
        account_history.save()
        return HttpResponseRedirect(reverse("account"))
    return HttpResponse("Add account history error")

def get_plot_data(request, year) -> JsonResponse:
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    
    accounts = Account.objects.filter(user=request.user)
    all_accounts_transactions = AccountTransaction.objects.annotate(year=ExtractYear('date')).filter(year=year, account__in=accounts)

    datasets = []
    for index, account in enumerate(accounts):
        annual_total = []
        for month in range(1, 13):
            monthly_total = all_accounts_transactions.filter(account=account, date__month=month).aggregate(Sum('amount'))['amount__sum']
            monthly_total = float(monthly_total or 0)

            annual_total.append(monthly_total)

        background_color, border_color = color_picker(index)
        dataset = {
            'label': account.name,
            'data': annual_total,
            'backgroundColor': background_color,
            'borderColor': border_color,
            'borderWidth': 1
        }
        datasets.append(dataset)
    return JsonResponse({'labels': month_list, 'datasets': datasets})

def get_table_data(request):
    year = request.GET.get('year', None)
    month = month_mapping(request.GET.get('month', None))
    account_name = request.GET.get('label', None)

    table_data = []
    if year and month and account_name:
        account = Account.objects.get(name=account_name)
        account_histories = AccountTransaction.objects.filter(account=account, date__year=year, date__month=month)

        for entry in account_histories:
            table_data.append({
                'id': entry.id,
                'date': format_date(entry.date),
                'amount': format_currency(entry.amount),
            })

    return JsonResponse(table_data, safe=False)

def update(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            for transaction_data in data:
                delete_bool = transaction_data.get("delete")
                transaction_id = transaction_data.get("id")
                account_name = transaction_data.get("filter")
                date = transaction_data.get("date")
                amount = float(transaction_data.get("amount").replace("$", "").replace(",", ""))

                if delete_bool:
                    AccountTransaction.objects.get(id=transaction_id).delete()
                    continue
                
                account = Account.objects.get(user=request.user, name=account_name)

                AccountTransaction.objects.update_or_create(
                    account = account,
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
def update_accounts(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            for transaction_data in data:
                request_user = transaction_data.get("user")
                delete_bool = transaction_data.get("delete")
                transaction_id = transaction_data.get("id")
                account_name = transaction_data.get("name")
                date = transaction_data.get("date")
                amount = float(transaction_data.get("balance").replace("$", "").replace(",", ""))
                
                if delete_bool:
                    AccountTransaction.objects.get(id=transaction_id).delete()
                    continue

                AccountTransaction.objects.update_or_create(
                    id=transaction_id,
                    defaults={
                        "date_history": date,
                        "balance_history": amount,
                        "account": Account.objects.get(user=request_user, name=account_name),
                    },
                )
            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

def plot_data(request):
    accounts_data, unique_years = get_accounts_data(request)
    return JsonResponse({"accounts_data": accounts_data, "years": unique_years})

