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
def view_accounts(request):
    accounts_data = get_latest_accounts_data(request)
    years = None
    if accounts_data:
        accounts_histories = AccountHistory.objects.filter(account__user=request.user)
        balance_history_df = pd.DataFrame.from_records(accounts_histories.values('account__name', 'balance_history', 'date_history'))
        balance_history_df['date_history'] = pd.to_datetime(balance_history_df['date_history'])
        balance_history_df['year'] = balance_history_df['date_history'].dt.year
        years =  sorted(balance_history_df['year'].unique(), reverse=True)

    return render(request, "accounts.html", {
        "networth": request.user.networth(),
        "accounts_data": accounts_data,
        "years": years,
        "today_date": datetime.today().strftime('%Y-%m-%d')
    })

def get_accounts_data_json(request):
    year = request.GET.get('year')
    label = request.GET.get('label')
    month_str = request.GET.get('month')
    month = month_mapping(month_str)
    print("Year: ", year, "Label: ", label, "Month: ", month)
    accounts_histories = AccountHistory.objects.filter(account__user=request.user)
    
    df = pd.DataFrame.from_records(
        accounts_histories.values('id', 'account__name', 'balance_history', 'date_history')
    )
    print("Balance History DF: ", df)
    df['date_history'] = pd.to_datetime(df['date_history'])
    df['Year'] = df['date_history'].dt.year
    df['Month'] = df['date_history'].dt.month
    df['Date'] = df['date_history']

    # Rename columns
    df = df.rename(columns={
        'account__name': 'Name',
        'balance_history': 'Balance',
    })

    df_filtered = df[df['Year'] == int(year)]
    df_filtered = df_filtered[df_filtered['Name'] == label]
    df_filtered = df_filtered[df_filtered['Month'] == int(month)]
    
    print("Filtered Accounts Data: ", df_filtered)
    df_filtered['Date'] = pd.to_datetime(df_filtered['Date']).dt.strftime('%Y-%m-%d')
    df_filtered['Balance'] = df_filtered['Balance'].apply(lambda x: f"${x:,.2f}")  # Format to 2 decimal places with currency symbol

 
    json_data = df_filtered[['id', 'Date', 'Name', 'Balance']].to_dict(orient='records')
    # json_data = _process_transaction_data(balance_history_df[['id', 'account__name', 'balance_history', 'Year', 'Date']], context="Accounts")

    print("Accounts Data JSON: ", df_filtered)
    return JsonResponse(json_data, safe=False)

# region Modification Functions
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
        # Create and save the account
        account = Account(
            user=request.user,
            type=account_type,
            name=account_name,
        )
        account.save()

        # Create and save the account history
        account_history = AccountHistory(
            account=account,
            balance_history=balance,
            date_history=balance_date,
        )
        account_history.save()
        
        return view_accounts(request)
    return HttpResponse("Add account error")

@login_required
def add_account_history(request):
    if request.method == "POST":
        print("Add Account History Request: ", request.POST)
        account = Account.objects.get(id=request.POST.get('account-id'))
        balance = request.POST.get('balance-input')
        date = request.POST.get('balance-date')

        account_history = AccountHistory(
            account=account,
            balance_history=balance,
            date_history=date,
        )
        account_history.save()
        return view_accounts(request)
    return HttpResponse("Add account history error")

@login_required
def update_accounts(request):
    if request.method == 'POST':
        try:
            # Decode the JSON body from the request
            data = json.loads(request.body.decode('utf-8'))
            print("Update Earnings Data: ", data)

            for transaction_data in data:
                # Extract the fields for each transaction
                request_user = transaction_data.get('user')
                delete_bool = transaction_data.get('delete')
                transaction_id = transaction_data.get('id') 
                account_name = transaction_data.get('name')
                date = transaction_data.get('date')
                amount = transaction_data.get('balance')
                amount = float(amount.replace('$', '').replace(',', ''))
                print("Update Account Data: ", delete_bool, transaction_id, account_name, date, amount)

                if delete_bool:
                    AccountHistory.objects.get(id=transaction_id).delete()
                    print("Account History Deleted: ", transaction_id)
                    continue
                
                account = Account.objects.get(user=request_user, name=account_name)
                print("Account: ", account)
                
                # Update Account and Account history
                AccountHistory.objects.update_or_create(
                    id=transaction_id,
                    defaults={
                        'date_history': date,
                        'balance_history': amount,
                        'account': account
                    }
                )

                print("Account History Updated: ", transaction_id, date, account_name, amount)

            return JsonResponse({'success': True})

        except Exception as e:
            print("Update Accounts Error: ", e)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

#endregion
# region Plotting Functions
@login_required
def plot_accounts_data(request):
    df = get_accounts_data_monthly_df(request)
    df['YearMonth'] = df['Date'].dt.to_period('M')
    df = df.sort_values('Date').drop_duplicates(['Account Name', 'YearMonth'], keep='last')
    df = df.drop(columns=['YearMonth'])
    years = df['Date'].dt.year.unique()
    json_data = []
    for year in years:
        df_year = df[df['Date'].dt.year == year]
        # Generating Labels (Months)
        labels = [calendar.month_abbr[i] for i in range(1, 13)]

        # Get Unique Account Names
        accounts_list = df_year['Account Name'].unique()

        datasets = []
        for i in range(len(accounts_list)):
            df_account = df_year[df_year["Account Name"] == accounts_list[i]]
            max_month = df_account['Month'].max()
            all_months = pd.DataFrame({'Month': range(1, max_month+1)})
            # # Merge the DataFrame with the complete list of months and fill missing values with 0
            df_complete = all_months.merge(df_account, on='Month', how='left').fillna(0)
            monthly_list = df_complete['Balance'].tolist()

            dataset = {
                "label": accounts_list[i],  # Dataset label
                "backgroundColor": color_picker(i)[0],  # Background color
                "borderColor": color_picker(i)[1],  # Border color
                "borderWidth": 1,
                "data": monthly_list
            }
            datasets.append(dataset)

        json_data.append({
            "year": int(year),
            "labels": labels[0:max_month],
            "data": datasets
        })

    return JsonResponse(json_data, safe=False)

@login_required
def plot_accounts_data_pie(request):
    accounts_list = list(Account.objects.filter(user=request.user))
    accounts_names_list = [account.name for account in accounts_list]
    data_list = []
    background_color_list = []
    border_color_list = []
    for i, account in enumerate (accounts_list):
        latest_balance = account.latest_balance
        print(account, "Latest Balance: ", latest_balance)
        data_list.append(account.latest_balance)
        background_color_list.append(color_picker(i)[0])
        border_color_list.append(color_picker(i)[1])

        datasets = [{
            "data": data_list,
            "backgroundColor": background_color_list,
            "borderColor": border_color_list 
        }]

    print("Datasets: ", datasets)

    # Structure the final response
    response_data = {
        "labels": accounts_names_list,
        "datasets": datasets
    }

    #print("Response Data: ", response_data)
    return JsonResponse(response_data, safe=False)

# endregion
