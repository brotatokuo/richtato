from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.db import IntegrityError
from django.http import JsonResponse
import pandas as pd
from django.db.models import Sum
import os, calendar
from viz.models import Category, Transaction, Account, User
from django.http import HttpResponse
from viz.utils import *
import json

@login_required
def view_settings(request):
    category_list = list(Category.objects.filter(user=request.user))
    return render(request, 'settings.html', {
        "account_types": account_choices,
        "category_list": category_list,
        "today_date": datetime.today().strftime('%Y-%m-%d'),
        "category_types": VARIANT_CHOICES
    })

@login_required
def get_card_settings_data_json(request):
    card_options = CardAccount.objects.filter(user=request.user).values('id', 'name').order_by('name')
    json_data = []
    for card in card_options:
        card_id = card['id']
        card_name = card['name']
        json_data.append({
            "Id": card_id,
            "Card": card_name
        })
    return JsonResponse(json_data, safe=False)

@login_required
def update_settings_card_account(request):
    if request.method == 'POST':
        try:
            # Decode the JSON body from the request
            data = json.loads(request.body.decode('utf-8'))
            print("Card Account Data: ", data)
            for card in data:
                # Extract the fields for each transaction
                delete_bool = card.get('delete')
                card_id = card.get('id')
                card_name = card.get('card').strip()
                print("Update Card Account: ", delete_bool, card_id, card_name)

                if delete_bool:
                    CardAccount.objects.get(id=card_id).delete()
                    print("Card Account Deleted: ", card_id)
                    continue

                CardAccount.objects.update_or_create(
                    user=request.user,
                    id=card_id,
                    defaults={
                        'name': card_name
                    }
                )

                print("Card Account Updated: ", card_id, card_name)
        
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_accounts_settings_data_json(request):
    accounts_data = get_latest_accounts_data(request)
    # print("Accounts Data: ", accounts_data)
    json_data = []
    for account in accounts_data:
        account_id = account['accounts_data']['account'].id
        account_name = account['account_name']
        account_type = account['accounts_data']['type']
        account_balance = account['accounts_data']['balance']
        account_date = account['accounts_data']['date']

        json_data.append({
            "Id": account_id,
            "Name": account_name,
            "Type": account_type,
            "Balance": account_balance,
            "Date": account_date,
        })
    
    return JsonResponse(json_data, safe=False)

@login_required
def update_settings_accounts(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            print("update_settings_accounts ", data)
            for account in data:
                delete_bool = account.get('delete')
                card_id = account.get('id')
                name = account.get('name').strip()
                account_type = account.get('type')


                if delete_bool:
                    Account.objects.get(id=card_id).delete()
                    print("Account Deleted: ", card_id)
                    continue
                
                account = Account.objects.get(id=card_id)
                account.name = name
                account.type = account_type
                account.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_categories_settings_data_json(request):
    category_options = Category.objects.filter(user=request.user).values('id', 'name', 'keywords', 'budget', 'variant').order_by('name')

    json_data = []
    for category in category_options:
        category_id = category['id']
        category_name = category['name']
        category_keywords = category['keywords']
        category_budget = category['budget']
        category_type = category['variant'].title()

        json_data.append({
            "Id": category_id,
            "Type": category_type,
            "Name": category_name,
            "Budget": category_budget,
            "Keywords": category_keywords,
        })
    
    return JsonResponse(json_data, safe=False)

@login_required
def update_settings_categories(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            print("Category Settings Data: ", data)
            for category in data:
                delete_bool = category.get('delete')
                category_id = category.get('id')
                category_name = category.get('name').strip()
                category_keywords = category.get('keywords').lower()
                category_budget = category.get('budget')
                category_type = category.get('type')

                if isinstance(category_keywords, str):
                    category_keywords = ','.join([kw.strip() for kw in category_keywords.split(',')])

                if delete_bool:
                    Category.objects.get(id=category_id).delete()
                    print("Category Deleted: ", category_id)
                    continue

                Category.objects.update_or_create(
                    user=request.user,
                    id=category_id,
                    defaults={
                        'name': category_name,
                        'keywords': category_keywords,
                        'budget': category_budget,
                        'variant': category_type
                    }
                )
        
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def add_category(request):
    if request.method=="POST":
        category_name = request.POST.get('category-name')
        keywords = request.POST.get('category-keywords').lower()
        budget = request.POST.get('category-budget')
        category_type = request.POST.get('category-type')

        if Category.objects.filter(user=request.user, name=category_name).exists():
            return HttpResponse("Category already exists, edit the existing category")
        category = Category(
            user=request.user,
            name=category_name,
            keywords=keywords,
            budget=budget,
            variant=category_type
        )
        category.save()
        
        return view_settings(request)
    return HttpResponse("Add category error")
@login_required
def add_card_account(request):
    if request.method=="POST":
        user_transactions = Transaction.objects.filter(user=request.user)
        all_accounts_names = [transaction.account_name for transaction in user_transactions]
        account_name = request.POST.get('account-name')

        # Check if account name already exists
        if account_name in all_accounts_names:
            return render(request, "settings.html",{
                "error_card_message": "Card Name already exists. Please choose a different name.",
            })
        
        # Create and save the Card account
        card_account = CardAccount(
            user=request.user,
            name=account_name,
        )
        card_account.save()
        
        return view_settings(request)
    return HttpResponse("Add account error")