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
def view_earnings(request):
    earnings_dates = Earning.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
    years_list = sorted(set(date.year for date in earnings_dates), reverse=True)
    account_names = Account.objects.filter(user=request.user)
    account_name_list = [account.name for account in account_names]
    entries = Earning.objects.filter(user=request.user).order_by('-date')
    print("Earnings Dates: ", earnings_dates)
    print("Accounts: ", account_name_list)
    print("Earnings Entries: ", entries)
    return render(request, 'earnings.html',
                  {"years": years_list,
                    "entries": entries,
                    "accounts": account_name_list,
                    "today_date": datetime.today().strftime('%Y-%m-%d')
                   })

@login_required
def add_earnings_entry(request):
    if request.method == "POST":
        # Get the form data
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        date = request.POST.get('balance-date')
        account = request.POST.get('account')

        account_name = Account.objects.get(user=request.user, name=account)
        # Create and save the transaction
        transaction = Earning(
            user=request.user,
            account_name = account_name,
            description=description,
            date=date,
            amount=amount,
        )
        transaction.save()
        return HttpResponseRedirect(reverse("view_earnings"))
    return HttpResponse("Data Entry Error")

@login_required
def plot_earnings_data(request, verbose=False):
    return plot_data(request, context="Earnings", group_by="Description", verbose=verbose)

@login_required
def update_earnings(request):
    if request.method == 'POST':
        try:
            print("Update Earnings Request: ")
            # Decode the JSON body from the request
            data = json.loads(request.body.decode('utf-8'))
            print("Update Earnings Data: ", data)

            for transaction_data in data:
                # Extract the fields for each transaction
                delete_bool = transaction_data.get('delete')
                transaction_id = transaction_data.get('id') 
                account_name = transaction_data.get('name')
                date = transaction_data.get('date')
                amount = transaction_data.get('amount')
                amount = float(amount.replace('$', '').replace(',', ''))

                if delete_bool:
                    Earning.objects.get(id=transaction_id).delete()
                    print("Earning Deleted: ", transaction_id)
                    continue

                Earning.objects.update_or_create(
                    user=request.user,
                    id=transaction_id,
                    defaults={
                        'date': date,
                        'amount': amount,
                    }
                )

                print("Transaction Updated: ", transaction_id, date, account_name, amount)

            return JsonResponse({'success': True})

        except Exception as e:

            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def get_earnings_data_json(request):
    year = request.GET.get('year')
    label = request.GET.get('label')
    month_str = request.GET.get('month')
    month = month_mapping(month_str)

    # Fetch the transaction data based on the user's context
    df = get_transaction_data(request.user, context="Earnings")

    # Filter data by year, label (description), and month
    df_filtered = df[df['Year'] == int(year)]
    df_filtered = df_filtered[df_filtered['Description'] == label]
    df_filtered = df_filtered[df_filtered['Month'] == int(month)]
    
    # Print filtered data for debugging
    print("Filtered Earnings Data: ", df_filtered)

    # Convert Date to 'YYYY-MM-DD' format and Balance to currency format
    df_filtered['Date'] = pd.to_datetime(df_filtered['Date']).dt.strftime('%Y-%m-%d')
    df_filtered['Amount'] = df_filtered['Amount'].apply(lambda x: f"${x:,.2f}")  # Format to 2 decimal places with currency symbol

    # Rename columns for JSON response
    df_filtered = df_filtered.rename(columns={
        'Account Name': 'Name',           
        'Date': 'Date',           
        'id': 'Id'                
    })

    json_data = df_filtered[['Id', 'Date', 'Name', 'Amount']].to_dict(orient='records')

    # Return JSON response
    return JsonResponse(json_data, safe=False)