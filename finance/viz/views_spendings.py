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
def view_spendings(request):
    if not isinstance(request.user, User):
        print(f"request.user is not a User instance: {request.user}")

    try:
        print("Request User: ", request.user)
        spending_dates = Transaction.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
        years_list = sorted(set(date.year for date in spending_dates), reverse=True)
        transaction_accounts = CardAccount.objects.filter(user=request.user).values_list('name', flat=True).distinct()
        category_list = list(Category.objects.filter(user=request.user).values_list('name', flat=True))
        print("Transaction Accounts: ", transaction_accounts)

    except Exception as e:
        print(f"Error while querying transactions: {e}")
        years_list = sorted(set(date.year for date in spending_dates)) if spending_dates else []
        transaction_accounts = CardAccount.objects.filter(user=request.user)\
                                                .values_list('name', flat=True)\
                                                .distinct()
        category_list = list(Category.objects.filter(user=request.user).values_list('name', flat=True))

    print("Transaction Accounts: ", transaction_accounts)
    return render(request, 'spendings.html',
                {"years": years_list,
                "transaction_accounts": transaction_accounts,
                "category_list": category_list,
                    "today_date": datetime.today().strftime('%Y-%m-%d')
                })

@login_required
def add_spendings_entry(request):
    if request.method == "POST":
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        date = request.POST.get('balance-date')
        category = request.POST.get('category')

        category = Category.objects.get(user=request.user, name=category)
        print("Category Search: ", category, type(category))
        account = request.POST.get('account')
        account_name = CardAccount.objects.get(user=request.user, name=account)

        transaction = Transaction(
            user=request.user,
            account_name = account_name,
            description=description,
            category=category,
            date=date,
            amount=amount,
        )
        transaction.save()
        return HttpResponseRedirect(reverse("view_spendings"))
    return HttpResponse("Data Entry Error")

@login_required
def plot_spendings_data(request, verbose=True):
    data_dict = plot_data(request, context="Spendings", group_by="Account Name", verbose=verbose)
    if verbose:
        print("Data Dict: ", data_dict)
    return data_dict

@login_required
def update_spendings(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            for transaction_data in data:
                delete_bool = transaction_data.get('delete')
                transaction_id = transaction_data.get('id') 
                account_name = transaction_data.get('name')
                description = transaction_data.get('description')
                date = transaction_data.get('date')
                amount = transaction_data.get('amount')
                amount = float(amount.replace('$', '').replace(',', ''))

                print("Update Spendings Data: ", delete_bool, transaction_id, account_name, description, date, amount)

                if delete_bool:
                    Transaction.objects.get(id=transaction_id).delete()
                    print("Transaction Deleted: ", transaction_id)
                    continue

                category_name = transaction_data.get('category') 
                category = Category.objects.get(user=request.user, name=category_name)
                account_name = CardAccount.objects.get(user=request.user, name=account_name)
                
                Transaction.objects.update_or_create(
                    user=request.user,
                    id=transaction_id,
                    defaults={
                        'date': date,
                        'description': description,
                        'amount': amount,
                        'category': category,
                        'account_name': account_name
                    }
                )
                print("Transaction Updated: ", transaction_id, date, description, amount, category, account_name)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def get_spendings_data_json(request):
    year = request.GET.get('year')
    label = request.GET.get('label')
    month_str = request.GET.get('month')
    month = month_mapping(month_str)
    print("Year: ", year, "Label: ", label, "Month: ", month)

    df = get_transaction_data(request.user, context="Spendings")

    df_filtered = df[df['Year'] == int(year)]
    df_filtered = df_filtered[df_filtered['Account Name'] == label]
    df_filtered = df_filtered[df_filtered['Month'] == int(month)]
    print("Filtered Spendings Data: ", df_filtered)

    df_filtered['Date'] = pd.to_datetime(df_filtered['Date']).dt.strftime('%Y-%m-%d')
    df_filtered['Amount'] = df_filtered['Amount'].apply(lambda x: f"${x:,.2f}")  # Format to 2 decimal places with currency symbol
    df_filtered = df_filtered.rename(columns={
        'Account Name': 'Name',           
        'Date': 'Date',           
        'id': 'Id'                
    })

    json_data = df_filtered[['Id', 'Date', 'Name', 'Description', 'Category', 'Amount']].to_dict(orient='records')

    # Return JSON response
    return JsonResponse(json_data, safe=False)
