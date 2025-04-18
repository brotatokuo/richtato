import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from richtato.apps.account.models import Account, AccountTransaction


@login_required
def add_entry(request):
    if request.method == "POST":
        try:
            account_name = request.POST.get("account-name")
            account_entity_id = request.POST.get("account-entity")
            asset_type_id = request.POST.get("asset-type")
            balance = request.POST.get("balance-input")
            date = request.POST.get("balance-date")

            if account_name in Account.objects.filter(user=request.user).values_list(
                "name", flat=True
            ):
                return HttpResponse("Account already exists", status=400)
            else:
                new_account = Account(
                    name=account_name,
                    asset_entity_name=account_entity_id,
                    type=asset_type_id,
                    user=request.user,
                    latest_balance=balance,
                    latest_balance_date=date,
                )

                account_history = AccountTransaction(
                    account=new_account,
                    amount=balance,
                    date=date,
                )
                new_account.save()
                account_history.save()
            return HttpResponseRedirect(reverse("account_settings"))
        except Account.DoesNotExist:
            return HttpResponse("Account not found", status=404)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=400)
    return HttpResponse("Invalid request method", status=405)


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
