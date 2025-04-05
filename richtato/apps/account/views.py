import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models.functions import ExtractYear
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse

from richtato.apps.account.models import Account, AccountTransaction
from richtato.utilities.tools import format_currency


@login_required
def main(request):
    account_options = Account.objects.filter(user=request.user).values_list(
        "id", "name"
    )
    unique_years = list(
        AccountTransaction.objects.filter(account__user=request.user)
        .annotate(Year=ExtractYear("date"))
        .values_list("Year", flat=True)
        .distinct()
        .order_by("-Year")
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


def update(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            for transaction_data in data:
                delete_bool = transaction_data.get("delete")
                transaction_id = transaction_data.get("id")
                account_name = transaction_data.get("filter")
                date = transaction_data.get("date")
                amount = float(
                    transaction_data.get("amount").replace("$", "").replace(",", "")
                )

                if delete_bool:
                    AccountTransaction.objects.get(id=transaction_id).delete()
                    continue

                account = Account.objects.get(user=request.user, name=account_name)

                AccountTransaction.objects.update_or_create(
                    account=account,
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
                amount = float(
                    transaction_data.get("balance").replace("$", "").replace(",", "")
                )

                if delete_bool:
                    AccountTransaction.objects.get(id=transaction_id).delete()
                    continue

                AccountTransaction.objects.update_or_create(
                    id=transaction_id,
                    defaults={
                        "date_history": date,
                        "balance_history": amount,
                        "account": Account.objects.get(
                            user=request_user, name=account_name
                        ),
                    },
                )
            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

    return JsonResponse({"success": False, "error": "Invalid request"})
    return JsonResponse({"success": False, "error": "Invalid request"})
    return JsonResponse({"success": False, "error": "Invalid request"})

    return JsonResponse({"success": False, "error": "Invalid request"})

    return JsonResponse({"success": False, "error": "Invalid request"})
    return JsonResponse({"success": False, "error": "Invalid request"})
