import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.db.models import Sum

from apps.account.models import Account
from apps.income.models import Income
from utilities.tools import month_mapping, format_currency, format_date


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
            print("Update Incomes Data: ", data)

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

                print(
                    "Expense Updated: ", transaction_id, date, account_name, amount
                )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
def get_plot_data(request, year):
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    accounts = Account.objects.filter(user=request.user)
    all_incomes = Income.objects.filter(user=request.user, date__year=year)
    
    datasets = []
    for account in accounts:
        income_list = []

        for month in range(1, 13): 
            total = all_incomes.filter(account_name=account, date__month=month).aggregate(Sum('amount'))['amount__sum']

            if total is None:
                total = 0
            
            income_list.append(total)

        # Build the dataset for the chart
        dataset = {
            'label': account.name,
            'data': income_list,
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        }
        datasets.append(dataset)

    return JsonResponse({'labels': month_list, 'datasets': datasets})

@login_required
def get_table_data(request):
    year = request.GET.get('year', None)
    month = month_mapping(request.GET.get('month', None))
    account = request.GET.get('label', None)

    table_data = []
    if year and month and account:
        incomes = Income.objects.filter(user=request.user, date__year=year, date__month=month, account_name__name=account)
        for income in incomes:
            table_data.append({
                'id': income.id,
                'date': format_date(income.date),
                'description': income.description,
                'amount': format_currency(income.amount),
            })

    return JsonResponse(table_data, safe=False)
