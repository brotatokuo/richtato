import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from apps.account.models import Account, AccountTransaction
from apps.expense.models import Expense
from apps.richtato_user.models import CardAccount, Category
from utilities.tools import format_currency, format_date


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

        all_accounts_names = CardAccount.objects.filter(user=request.user).values_list('name', flat=True)
        if account_name in all_accounts_names:
            return render(
                request,
                "settings.html",
                {
                    "error_card_message": "Card Name already exists. Please choose a different name.",
                },
            )

        # Create and save the Card account
        card_account = CardAccount(
            user=request.user,
            name=account_name,
        )
        card_account.save()

        return main(request)
    return HttpResponse("Add account error")

@login_required
def update_cards(request):
    if request.method == "POST":
        try:
            # Decode the JSON body from the request
            data = json.loads(request.body.decode("utf-8"))
            print("Card Account Data: ", data)
            for card in data:
                # Extract the fields for each transaction
                delete_bool = card.get("delete")
                card_id = card.get("id")
                card_name = card.get("card").strip()
                print("Update Card Account: ", delete_bool, card_id, card_name)

                if delete_bool:
                    CardAccount.objects.get(id=card_id).delete()
                    print("Card Account Deleted: ", card_id)
                    continue

                CardAccount.objects.update_or_create(
                    user=request.user, id=card_id, defaults={"name": card_name}
                )

                print("Card Account Updated: ", card_id, card_name)

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
                "Date":format_date(account.latest_balance_date),
            }
        )
    return JsonResponse(json_data, safe=False)

# @login_required
# def _get_latest_accounts_data(request)->JsonResponse:
#     user_accounts = request.user.account.all()
#     user_accounts = sorted(user_accounts, key=lambda x: x.name)
#     json_data = []
#     for account in user_accounts:
#         # Get the latest balance history record for the account
#         balance_history = account.history.all()
#         balance_list = []
#         date_list = []

#         for history in balance_history:
#             balance_list.append(history.balance_history)  # Add balance to list
#             date_list.append(history.date_history)  # Add date to list

#         sorted_history = sorted(zip(date_list, balance_list), key=lambda x: x[0], reverse=True)
#         date_list_sorted, balance_list_sorted = zip(*sorted_history) if sorted_history else ([], [])
#         latest_date = date_list_sorted[0] if date_list_sorted else None
#         latest_balance = balance_list_sorted[0] if balance_list_sorted else None

#         accounts_data = {
#             'id': account.id,
#             'account': account,
#             'type': account.get_type_display(),
#             'balance': format_currency(latest_balance),
#             'date': latest_date,
#             'history': list(zip(balance_list, date_list)) 
#         }
#         json_data.append({
#             "account_name": account.name,
#             "accounts_data": accounts_data})
#     return json_data

@login_required
def add_account(request):
    if request.method=="POST":
        all_accounts_names = [account.name for account in request.user.account.all()]

        account_type = request.POST.get('account-type')
        account_name = request.POST.get('account-name')
        balance_date = request.POST.get('balance-date')
        balance = request.POST.get('balance-input')

        if account_name in all_accounts_names:
            print("Account name already exists. Please choose a different name.")
            return render(request, "settings.html",{
                "error_account_message": "Account name already exists. Please choose a different name.",
            })

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
        
        return main(request)
    return HttpResponse("Add account error")

@login_required
def update_accounts(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            print("update_settings_accounts ", data)
            for account in data:
                delete_bool = account.get("delete")
                card_id = account.get("id")
                name = account.get("name").strip()
                account_type = account.get("type")

                if delete_bool:
                    Account.objects.get(id=card_id).delete()
                    print("Account Deleted: ", card_id)
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
            for category in data:
                delete_bool = category.get("delete")
                category_id = category.get("id")
                category_name = category.get("name").strip()
                category_keywords = category.get("keywords").lower()
                category_budget = category.get("budget")
                category_type = category.get("type")
                category_color = category.get("color")

                if isinstance(category_keywords, str):
                    category_keywords = ",".join(
                        [kw.strip() for kw in category_keywords.split(",")]
                    )

                if delete_bool:
                    Category.objects.get(id=category_id).delete()
                    print("Category Deleted: ", category_id)
                    continue

                Category.objects.update_or_create(
                    user=request.user,
                    id=category_id,
                    defaults={
                        "name": category_name,
                        "keywords": category_keywords,
                        "budget": category_budget,
                        "variant": category_type,
                        "color": category_color,
                    },
                )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})
# endregion
