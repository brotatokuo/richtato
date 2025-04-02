import decimal
import json
from datetime import datetime

import colorama
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse

from richtato.apps.account.models import Account, AccountTransaction
from richtato.apps.richtato_user.models import CardAccount, Category
from richtato.apps.settings.models import DataImporter
from richtato.utilities.tools import format_currency, format_date


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
@login_required
def get_cards(request):
    card_options = (
        CardAccount.objects.filter(user=request.user)
        .values("id", "name")
        .order_by("name")
    )
    json_data = []
    for card in card_options:
        card_id = card["id"]
        card_name = card["name"]
        json_data.append({"Id": card_id, "Card": card_name})

    return JsonResponse(json_data, safe=False)


@login_required
def add_card(request):
    if request.method == "POST":
        account_name = request.POST.get("account-name").strip()

        all_accounts_names = CardAccount.objects.filter(user=request.user).values_list(
            "name", flat=True
        )
        if account_name in all_accounts_names:
            return render(
                request,
                "account_settings.html",
                {
                    "error_card_message": "Card Name already exists. Please choose a different name.",
                },
            )

        card_account = CardAccount(
            user=request.user,
            name=account_name,
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

                if delete_bool:
                    CardAccount.objects.get(id=card_id).delete()
                    continue

                CardAccount.objects.update_or_create(
                    user=request.user, id=card_id, defaults={"name": card_name}
                )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


# endregion


# region Account
@login_required
def get_accounts(request):
    accounts = Account.objects.filter(user=request.user)
    json_data = []
    for account in accounts:
        json_data.append(
            {
                "Id": account.id,
                "Name": account.name,
                "Type": account.type,
                "Balance": format_currency(account.latest_balance),
                "Date": format_date(account.latest_balance_date)
                if account.latest_balance_date
                else None,
            }
        )
    return JsonResponse(json_data, safe=False)


@login_required
def add_account(request):
    if request.method == "POST":
        all_accounts_names = [account.name for account in request.user.account.all()]

        account_type = request.POST.get("account-type")
        account_name = request.POST.get("account-name")
        balance_date = request.POST.get("balance-date")
        balance = request.POST.get("balance-input")

        if account_name in all_accounts_names:
            return render(
                request,
                "settings.html",
                {
                    "error_account_message": "Account name already exists. Please choose a different name.",
                },
            )

        account = Account(
            user=request.user,
            type=account_type,
            name=account_name,
            latest_balance=balance,
            latest_balance_date=balance_date,
        )
        account.save()

        account_history = AccountTransaction(
            account=account,
            amount=balance,
            date=balance_date,
        )
        account_history.save()

        return HttpResponseRedirect(reverse("settings"))
    return HttpResponse("Add account error")


@login_required
def update_accounts(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            for account in data:
                delete_bool = account.get("delete")
                card_id = account.get("id")
                name = account.get("name").strip()
                account_type = account.get("type")

                if delete_bool:
                    Account.objects.get(id=card_id).delete()
                    continue

                account = Account.objects.get(id=card_id)
                account.name = name
                account.type = account_type
                account.save()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


# endregion


# region Categories
@login_required
def get_categories(request):
    category_options = (
        Category.objects.filter(user=request.user)
        .values("id", "name", "keywords", "budget", "type", "color")
        .order_by("name")
    )

    json_data = []
    for category in category_options:
        category_id = category["id"]
        category_name = category["name"]
        category_keywords = category["keywords"]
        category_budget = category["budget"]
        category_type = category["type"].title()
        color = category["color"]

        json_data.append(
            {
                "Id": category_id,
                "Type": category_type,
                "Name": category_name,
                "Budget": format_currency(category_budget),
                "Keywords": category_keywords,
                "Color": color,
            }
        )

    return JsonResponse(json_data, safe=False)


@login_required
def add_category(request):
    if request.method == "POST":
        category_name = request.POST.get("category-name")
        keywords = request.POST.get("category-keywords").lower()
        budget = request.POST.get("category-budget")
        category_type = request.POST.get("category-type")

        if Category.objects.filter(user=request.user, name=category_name).exists():
            return HttpResponse("Category already exists, edit the existing category")
        category = Category(
            user=request.user,
            name=category_name,
            keywords=keywords,
            budget=budget,
            type=category_type,
        )
        category.save()

        return main(request)
    return HttpResponse("Add category error")


@login_required
def update_categories(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            print("Data:", data)
            for category in data:
                delete_bool = category.get("delete")
                category_id = category.get("id")
                category_name = category.get("name").strip()
                category_keywords = category.get("keywords").lower()
                category_budget_str = category.get("budget")
                category_budget = decimal.Decimal(
                    category_budget_str.replace("$", "").replace(",", "").strip()
                )
                category_type = category.get("type")
                category_color = category.get("color")

                if delete_bool:
                    Category.objects.get(id=category_id).delete()
                    continue

                try:
                    Category.objects.update_or_create(
                        user=request.user,
                        id=category_id,
                        defaults={
                            "name": category_name,
                            "keywords": category_keywords,
                            "budget": category_budget,
                            "type": category_type,
                            "color": category_color,
                        },
                    )
                    print(colorama.Fore.GREEN + "Categories updated successfully")
                except Exception as e:
                    print(colorama.Fore.RED + "Error updating category:", e)

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


# endregion


# region Import
@login_required
def generate_csv_templates(request):
    if request.method == "POST":
        path = request.POST.get("path")
        request.user.import_path = path
        request.user.save()
        DataImporter(
            user=request.user, path=request.user.import_path
        ).generate_csv_templates()
        return HttpResponseRedirect(reverse("settings"))
    return HttpResponseRedirect(reverse("settings"))


@login_required
def import_csv(request):
    if request.method == "POST":
        path = request.POST.get("import-folder")
        request.user.import_path = path
        print("Path:", path)
        request.user.save()
        importer = DataImporter(user=request.user, path=request.user.import_path)
        print("Importing from CSV")
        importer.import_from_csv()
        return HttpResponseRedirect(reverse("settings"))
    return HttpResponseRedirect(reverse("settings"))
    return HttpResponseRedirect(reverse("settings"))
    return HttpResponseRedirect(reverse("settings"))
