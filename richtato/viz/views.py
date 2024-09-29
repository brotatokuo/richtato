# Richtato/views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.db import IntegrityError
from django.http import JsonResponse
import random, pandas as pd
import os, calendar
from viz.models import Category, Transaction, Account, User
from django.http import HttpResponse
from viz.utils import *
import json

from django.contrib.auth import get_user_model
User = get_user_model() 
pd.set_option('future.no_silent_downcasting', True)

data_folder_path = os.path.join(parent_path, "static/data")
card_statements_folder_path = os.path.join(data_folder_path, "Credit Card Statements")
file_name = "master_creditcard_data.xlsx"
data_file_path = os.path.join(data_folder_path, file_name)

# region pages
def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "login.html", {
                "username": username,
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html",{
            "username": '',
            "message": None,
    })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["password2"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })
        else:
            print("Passwords match")

        # Attempt to create new user
        try:
            print("Attempting to create user: ", username)
            user = User.objects.create_user(
                username=username,
                password=password
            )        
            user.save()
            print("user created: ", username)

        except IntegrityError:
            print("Username already taken")
            return render(request, "register.html", {
                "message": "Username already taken."
            })

        except Exception as e:
            print(f"Error creating user: {e}")  # Log the error
            return render(request, "register.html", {
                "message": "An error occurred during registration."
            })

        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "register.html")

@login_required
def spendings(request):
    spending_dates = Transaction.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
    years_list = sorted(set(date.year for date in spending_dates))
    transaction_accounts = CardAccount.objects.filter(user=request.user).values_list('name', flat=True).distinct()
    category_list = list(Category.objects.filter(user=request.user).values_list('name', flat=True))

    print("Transaction Accounts: ", transaction_accounts)
    return render(request, 'spendings.html',
                  {"years": years_list,
                   "transaction_accounts": transaction_accounts,
                   "category_list": category_list,
                   })

@login_required
def earnings(request):
    earnings_dates = Earning.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
    years_list = sorted(set(date.year for date in earnings_dates))
    account_names = Account.objects.filter(user=request.user)
    account_name_list = [account.name for account in account_names]
    entries = Earning.objects.filter(user=request.user).order_by('-date')
    print("Earnings Dates: ", earnings_dates)
    print("Accounts: ", account_name_list)
    print("Earnings Entries: ", entries)
    return render(request, 'earnings.html'  ,
                  {"years": years_list,
                    "entries": entries,
                    "accounts": account_name_list,
                   })

@login_required
def spending_entry(request):
    transaction_accounts = Transaction.objects.filter(user=request.user).values_list('account_name', flat=True).distinct()
    entries = Transaction.objects.filter(user=request.user).exclude(category="Earnings").order_by('-date')
    print(entries)
    return render(request, 'spending_entry.html',
                  {"entries": entries,
                     "transaction_accounts": transaction_accounts,
                   })

@login_required
def settings(request):
    card_options = list(CardAccount.objects.filter(user=request.user).values_list('name', flat=True))
    print("Card Options: ", card_options)
    accounts_data = get_latest_accounts_data(request)
    account_types = account_choices
    category_list = list(Category.objects.filter(user=request.user))
    print("Category List: ", category_list)
    return render(request, 'settings.html', {
        "card_options": card_options,
        "accounts_data": accounts_data,
        "account_types": account_types,
        "category_list": category_list
    })

@login_required
def accounts(request):
    accounts_data = get_latest_accounts_data(request)
    print("Accounts Data: ", accounts_data)
    return render(request, "accounts.html", {
        "networth": request.user.networth(),
        "accounts_data": accounts_data,
    })

@login_required
def import_statements_data(request):
    sort_statements()
    compiled_df = compile_statements()
    df = categorize_transactions(compiled_df)
    post_to_sql(df, request.user)
    return HttpResponse("Renamed Statements and added to SQL database")

@login_required
def export_statements_data(request):
    transactions_df = get_sql_data(request.user, context="Transactions")
    earnings_df = get_sql_data(request.user, context="Earnings")
    accounts_df = get_accounts_data_monthly_df(request)

@login_required
def data(request):
    return render(request, 'data.html')
# endregion

# region Data Routes
@login_required
def get_latest_accounts_data(request):
    user_accounts = request.user.account.all()
    accounts_data = []
    for account in user_accounts:
        # Get the latest balance history record for the account
        balance_history = account.history.all()
        balance_list = []
        date_list = []

        for history in balance_history:
            balance_list.append(history.balance_history)  # Add balance to list
            date_list.append(history.date_history)  # Add date to list

        # Zip the balance and date lists together, then sort by the date
        sorted_history = sorted(zip(date_list, balance_list), key=lambda x: x[0], reverse=True)

        # Unzip the sorted result back into separate lists (if you need them)
        date_list_sorted, balance_list_sorted = zip(*sorted_history) if sorted_history else ([], [])

        # Get the latest balance and date
        latest_date = date_list_sorted[0] if date_list_sorted else None
        latest_balance = balance_list_sorted[0] if balance_list_sorted else None

        # Collect the necessary data for each account
        accounts_data.append({
            'account': account,
            'balance': latest_balance,
            'date': latest_date,
            'history': list(zip(balance_list, date_list)) 
        })

        return accounts_data

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
        
        return accounts(request)
    return HttpResponse("Add account error")

@login_required
def update_accounts(request):
    if request.method=="POST":
        account_id = request.POST.get('account-id')
        balance_date = request.POST.get('balance-date')
        balance = request.POST.get('balance-input')
        # Get the account
        account = Account.objects.get(user=request.user, id=account_id)

        print("Update account details: ", account, balance_date, balance)
        # Update the account history
        account_history = AccountHistory(
            account=account,
            balance_history=balance,
            date_history=balance_date,
        )
        account_history.save()
        return accounts(request)

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
        
        return settings(request)
    return HttpResponse("Add account error")

# region Plotting
@login_required
def plot_earnings_data(request):
    return plot_data(request, context="Earnings", group_by="Description")

@login_required
def plot_spendings_data(request):
    return plot_data(request, context="Spending", group_by="Account Name")

@login_required
def plot_data(request, context, group_by):
    df = get_sql_data(request.user, context=context)
    if df.empty:
        print("\033[91mviews.py - plot_data: No data available. Please import data first.\033[0m")
    else:
        # Generating Labels (Months)
        labels = [calendar.month_abbr[i] for i in range(1, 13)]

        # Get Unique Account Names
        group_list = df[group_by].unique()
        #print("Unique Accounts: ", group_list)

        datasets = []
        for i in range(len(group_list)):
            df_account = df[df[group_by] == group_list[i]]
            df_monthly_sum = df_account.groupby('Month')['Amount'].sum().reset_index()
            max_month = df_monthly_sum['Month'].max()
            all_months = pd.DataFrame({'Month': range(1, max_month+1)})
            df_complete = all_months.merge(df_monthly_sum, on='Month', how='left').fillna(0)
            monthly_spending_sum_list = df_complete['Amount'].tolist()

            dataset = {
                "label": group_list[i],  # Dataset label
                "backgroundColor": color_picker(i)[0],  # Background color
                "borderColor": color_picker(i)[1],  # Border color
                "borderWidth": 1,
                "data": monthly_spending_sum_list
            }
            datasets.append(dataset)

        # Structure the final response
        response_data = {
            "labels": labels[0:max_month],
            "datasets": datasets
        }
        #print("Response Data: ", response_data)
        # print("Response Data: ", response_data)
        return JsonResponse(response_data, safe=False)

# endregion

@login_required
def get_sql_data_json(request, verbose=False):
    df = get_sql_data(request.user)
    if verbose:
        print("get_sql_data_json: ", df)
    if df.empty:
        return {}
    df["Description"] = df["Description"].str.slice(0, 20)
    df = df[df["Category"] != "Earnings"]
    df_json = df.to_dict(orient='records')
    return JsonResponse(df_json, safe=False)

@login_required
def get_sql_data_json_earnings(request):
    df = get_sql_data(request.user, context="Earnings")
    if df.empty:
        return {}
    df["Description"] = df["Description"].str.slice(0, 20)
    df_json = df.to_dict(orient='records')  
    return JsonResponse(df_json, safe=False)

@login_required
def get_accounts_data_monthly_df(request):
    users_accounts = Account.objects.filter(user=request.user)
    master_df = pd.DataFrame()
    for account in users_accounts:
        df = pd.DataFrame()
        
        balance_history = account.history.all()
        balance_history_df = pd.DataFrame(balance_history.values())

        df["Date"] = pd.to_datetime(balance_history_df['date_history'])
        df["Balance"] = balance_history_df['balance_history']
        df["Account Name"] = account.name
        master_df = pd.concat([master_df, df])

    # Organizing the data

    master_df['Month'] = master_df['Date'].dt.month
    return master_df

@login_required
def get_accounts_data_json(request):
    users_accounts = Account.objects.filter(user=request.user)
    json_data = {}
    for account in users_accounts:
        balance_history = account.history.all()
        balance_history_df = pd.DataFrame(balance_history.values())
        balance_history_df['date_history'] = pd.to_datetime(balance_history_df['date_history'])
        balance_history_df.drop('id', axis=1, inplace=True)

        json_data[account.name] = {
            "name": account.name,
            "balance_list": balance_history_df['balance_history'].tolist(),
            "date_list": balance_history_df['date_history'].dt.strftime('%Y-%m-%d').tolist()
        }

    return JsonResponse(json_data, safe=False)

@login_required
def plot_accounts_data(request):
    df = get_accounts_data_monthly_df(request)
    # Generating Labels (Months)
    labels = [calendar.month_abbr[i] for i in range(1, 13)]

    # Get Unique Account Names
    accounts_list = df['Account Name'].unique()
    #print("Unique Accounts: ", accounts_list)

    datasets = []
    for i in range(len(accounts_list)):
        df_account = df[df["Account Name"] == accounts_list[i]]

        df_monthly_sum = df_account.groupby('Month')['Balance'].sum().reset_index()
        max_month = df_monthly_sum['Month'].max()

        all_months = pd.DataFrame({'Month': range(1, max_month+1)})
        # # Merge the DataFrame with the complete list of months and fill missing values with 0
        df_complete = all_months.merge(df_monthly_sum, on='Month', how='left').fillna(0)
        monthly_list = df_complete['Balance'].tolist()

        dataset = {
            "label": accounts_list[i],  # Dataset label
            "backgroundColor": color_picker(i)[0],  # Background color
            "borderColor": color_picker(i)[1],  # Border color
            "borderWidth": 1,
            "data": monthly_list
        }
        datasets.append(dataset)

        #print(datasets)
    # Structure the final response
    response_data = {
        "labels": labels[0:max_month],
        "datasets": datasets
    }
    # print("Response Data: ", response_data)
    return JsonResponse(response_data, safe=False)

@login_required
def plot_accounts_data_pie(request):
    df = get_accounts_data_monthly_df(request)
    
    # Get Unique Account Names
    accounts_list = df['Account Name'].unique()
    #print("Unique Accounts: ", accounts_list)

    data_list = []
    background_color_list = []
    border_color_list = []

    for i in range(len(accounts_list)):
        df_account = df[df["Account Name"] == accounts_list[i]]

        df_account = df_account.sort_values(by='Date')
        latest_balance = df_account['Balance'].iloc[-1]
        balance_date = df_account['Date'].iloc[-1]

        data_list.append(latest_balance)
        background_color_list.append(color_picker(i)[0])
        border_color_list.append(color_picker(i)[1])

    datasets = [{
        "data": data_list,
        "backgroundColor": background_color_list,
        "borderColor": border_color_list 
    }]

    # Structure the final response
    response_data = {
        "labels": accounts_list.tolist(),
        "datasets": datasets
    }

    #print("Response Data: ", response_data)
    return JsonResponse(response_data, safe=False)

@login_required
def spending_data_entry(request):
    if request.method == "POST":
        # Get the form data
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        category = request.POST.get('category')

        category = Category.objects.get(name=category)
        print("Category Search: ", category, type(category))
        account = request.POST.get('account')
        account_name = CardAccount.objects.get(name=account)

        # Create and save the transaction
        transaction = Transaction(
            user=request.user,
            account_name = account_name,
            description=description,
            category=category,
            date=date,
            amount=amount,
        )
        transaction.save()
        return HttpResponseRedirect(reverse("spendings"))
    return HttpResponse("Data Entry Error")

@login_required
def earnings_data_entry(request):
    if request.method == "POST":
        # Get the form data
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        account = request.POST.get('account')

        account_name = Account.objects.get(name=account)
        # Create and save the transaction
        transaction = Earning(
            user=request.user,
            account_name = account_name,
            description=description,
            date=date,
            amount=amount,
        )
        transaction.save()
        return HttpResponseRedirect(reverse("earnings"))
    return HttpResponse("Data Entry Error")

@login_required
def update_row(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        updated_data = data.get('data')
        updated_category = updated_data.get("column_0")
        updated_keywords = updated_data.get("column_1")

        print("Updated Data: ", updated_data)
        print("Updated Category: ", updated_category)
        print("Updated Keywords: ", updated_keywords)
        # Using get_or_create to simplify logic
        category, created = Category.objects.get_or_create(
            user=request.user,
            name=updated_category,
            defaults={'keywords': updated_keywords}
        )

        if not created:
            category.keywords = updated_keywords
            category.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def delete_row(request):
    if request.method == 'POST':
        # Parse the incoming JSON data
        data = json.loads(request.body.decode('utf-8'))
        # Get the row ID and updated data

        updated_data = data.get('data')
        print("Updated Data: ", updated_data)
        updated_category = updated_data.get("column_0")
        updated_keywords = updated_data.get("column_1")
        print("Updated Category: ", updated_category)
        print("Updated Keywords: ", updated_keywords)
        try:
            # Find the object to update
            category = Category.objects.get(name=updated_category)

            category.delete()

            # Respond with success
            return JsonResponse({'success': True})

        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})