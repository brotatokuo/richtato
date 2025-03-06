import json
import os
from datetime import datetime

from apps.account.models import Account, AccountTransaction
from apps.richtato_user.models import CardAccount, CardAccountDB, Category, CategoryDB
from apps.settings.models import DataImporter
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from loguru import logger
from utilities.tools import convert_currency_to_str_float, format_date


@login_required
def main(request):
    category_list = list(Category.objects.filter(user=request.user))
    return render(
        request,
        "settings.html",
        {
            "account_types": Account.ACCOUNT_TYPES,
            "category_list": category_list,
            "today_date": datetime.today().strftime("%Y-%m-%d"),
            "category_types": Category.CATEGORY_TYPES,
            "google_sheets_link": request.user.google_sheets_link,
            "deploy_stage": os.getenv("DEPLOY_STAGE"),
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
        account_name = request.POST.get("account-name")
        CardAccountDB(request.user).add(account_name)
        return HttpResponseRedirect(reverse("settings"))
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
                    CardAccountDB(request.user).delete(card_id=card_id)
                    continue
                else:
                    CardAccountDB(request.user).update(card_id, card_name)

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


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
                "Balance": convert_currency_to_str_float(account.latest_balance),
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
                if delete_bool:
                    Account.objects.get(id=card_id).delete()
                    continue

                name = account.get("name")
                account_type = account.get("type")
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
                "Budget": convert_currency_to_str_float(category_budget),
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
        CategoryDB(request.user).add(category_name, keywords, budget, category_type)
    return main(request)


@login_required
def update_categories(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            print("Data:", data)
            for category in data:
                delete_bool = category.get("delete")
                category_name = category.get("name").strip()
                if delete_bool:
                    CategoryDB(request.user).delete(category_name)
                    continue

                category_keywords = category.get("keywords").lower()
                category_budget = category.get("budget")
                category_type = category.get("type")
                category_color = category.get("color")

                try:
                    CategoryDB(request.user).update(
                        category_name,
                        category_keywords,
                        category_budget,
                        category_type,
                        category_color,
                    )
                    logger.debug("Categories updated successfully")
                except Exception as e:
                    logger.error("Error updating category:", e)

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
