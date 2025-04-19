import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse

from richtato.apps.account.models import Account
from richtato.apps.richtato_user.models import CardAccount, Category


def main(request):
    category_list = list(Category.objects.filter(user=request.user))
    return render(
        request,
        "old_settings.html",
        {
            "account_types": Account.account_types,
            "category_list": category_list,
            "today_date": datetime.today().strftime("%Y-%m-%d"),
            "category_types": Category.CATEGORY_TYPES,
        },
    )


# region Card Accounts
def get_cards(request):
    card_options = CardAccount.objects.filter(user=request.user).order_by("name")

    data = []
    for card in card_options:
        data.append(
            {
                "id": card.id,
                "card": card.name,
                "bank": card.card_bank_title,
            }
        )

    columns = [
        {"title": "ID", "data": "id"},
        {"title": "Card", "data": "card"},
        {"title": "Bank", "data": "bank"},
    ]

    return JsonResponse({"columns": columns, "data": data})


@login_required
def add_card(request):
    if request.method == "POST":
        card_name = request.POST.get("card-name").strip()
        card_bank = request.POST.get("card-bank").strip()

        all_accounts_names = CardAccount.objects.filter(user=request.user).values_list(
            "name", flat=True
        )
        if card_name in all_accounts_names:
            return render(
                request,
                "account_settings.html",
                {
                    "error_card_message": "Card Name already exists. Please choose a different name.",
                },
            )

        card_account = CardAccount(
            user=request.user,
            name=card_name,
            card_bank=card_bank,
        )
        card_account.save()

        return HttpResponseRedirect(reverse("account_settings"))
    return HttpResponse("Add account error")


@login_required
def update_cards(request):
    if request.method == "POST":
        try:
            # Decode the JSON body from the request
            data = json.loads(request.body.decode("utf-8"))
            for card in data:
                # Extract the fields for each transaction
                delete_bool = card.get("delete")
                card_id = card.get("id")
                card_name = card.get("card").strip()
                card_bank = card.get("bank").strip()

                if delete_bool:
                    CardAccount.objects.get(id=card_id).delete()
                    continue

                CardAccount.objects.update_or_create(
                    user=request.user,
                    id=card_id,
                    defaults={"name": card_name, "card_bank": card_bank},
                )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


# endregion
