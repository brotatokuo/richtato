# Richtato/views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.db import IntegrityError
from django.http import JsonResponse
import random, pandas as pd
from django.db.models import Sum
import os, calendar
from viz.models import Category, Transaction, Account, User
from django.http import HttpResponse
from viz.utils import *
import json


data_folder_path = os.path.join(parent_path, "static/data")
card_statements_folder_path = os.path.join(data_folder_path, "Credit Card Statements")
file_name = "master_creditcard_data.xlsx"
data_file_path = os.path.join(data_folder_path, file_name)

# region Main Pages
def view_index(request):
    return render(request, 'index.html')

def view_login(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("view_index"))
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

def view_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse("view_index"))

def view_register(request):
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
        return HttpResponseRedirect(reverse("view_index"))
    else:
        return render(request, "register.html")

@login_required
def view_budget(request):
    spending_dates = Transaction.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
    years_list = sorted(set(date.year for date in spending_dates), reverse=True)
    months_list = sorted(set(date.month for date in spending_dates), reverse=True)
    category_list = list(Category.objects.filter(user=request.user).values_list('name', flat=True))

    print("Budget Years: ", years_list)
    print("Budget Months: ", months_list)
    return render(request, 'budget.html',
                  {"years": years_list,
                   "months": months_list,
                   "categories": category_list
                   })

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
def view_accounts(request):
    accounts_data = get_latest_accounts_data(request)
    years = None
    if accounts_data:
        accounts_histories = AccountHistory.objects.filter(account__user=request.user)
        balance_history_df = pd.DataFrame.from_records(accounts_histories.values('account__name', 'balance_history', 'date_history'))
        # Convert dates to datetime
        balance_history_df['date_history'] = pd.to_datetime(balance_history_df['date_history'])
        # Extract year and month-day for labels
        balance_history_df['year'] = balance_history_df['date_history'].dt.year
        years =  sorted(balance_history_df['year'].unique(), reverse=True)

    return render(request, "accounts.html", {
        "networth": request.user.networth(),
        "accounts_data": accounts_data,
        "years": years,
        "today_date": datetime.today().strftime('%Y-%m-%d')
    })

@login_required
def view_settings(request):
    category_list = list(Category.objects.filter(user=request.user))
    return render(request, 'settings.html', {
        "account_types": account_choices,
        "category_list": category_list,
        "import_path": card_statements_folder_path,
        "export_path": data_folder_path,
        "today_date": datetime.today().strftime('%Y-%m-%d'),
        "category_types": VARIANT_CHOICES
    })
# region Budget
@login_required
def get_budget_months(request):
    year = request.GET.get('year')
    print("Get Budget Months: ", year)

    # Filter transactions by year and get relavant months
    months = sorted(list(Transaction.objects.filter(user=request.user, date__year=year).dates('date', 'month').values_list('date__month', flat=True)), reverse=True)
    print("Months: ", months)
    return JsonResponse(months, safe=False)

@login_required
def plot_budget_data(request):
    print("Plot Budget Data")
    years = list(Transaction.objects.filter(user=request.user).exclude(date__isnull=True).dates('date', 'year').values_list('date__year', flat=True))
    json_data = []
    for year in years:
        months = list(Transaction.objects.filter(user=request.user, date__year=year).dates('date', 'month').values_list('date__month', flat=True))

        month_data = []
        for month in months:
            transactions = Transaction.objects.filter(user=request.user, date__year=year, date__month=month)
            categories = list(transactions.values_list('category__name', flat=True).distinct())
            category_percentages_dataset = []
            for index, category in enumerate(categories):
                category_transactions = transactions.filter(category__name=category)
                category_sum = category_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
                category_budget = Category.objects.get(user=request.user, name=category).budget
                category_budget_percent = round(category_sum * 100 / category_budget)
                data_placeholder = [0] * len(categories)
                data_placeholder[index] = category_budget_percent
                category_percentages_datapoint = {
                    'label': category,
                    'backgroundColor': color_picker(index)[0],
                    'borderColor': color_picker(index)[1],
                    'borderWidth': 1,
                    'data': data_placeholder
                }
                category_percentages_dataset.append(category_percentages_datapoint)
                
            data = {
                'labels': categories,
                'datasets': category_percentages_dataset
            }
            month_data.append({
                'month': month,
                'data': data
            })
        json_data.append({
            'year': year,
            'data': month_data
        })
    return JsonResponse(json_data, safe=False)

@login_required
def get_budget_data_json(request):
    print("Get Budget Table Data")
    year = request.GET.get('year')
    label = request.GET.get('label')
    month = request.GET.get('month')

    print("Year: ", year, "Label: ", label, "Month: ", month)
    df = get_transaction_data(request.user, context="Spendings")

    # Filter data by year, label (description), and month
    df_filtered = df[df['Year'] == int(year)]
    df_filtered = df_filtered[df_filtered['Category'] == label]
    df_filtered = df_filtered[df_filtered['Month'] == int(month)]
    
    # Print filtered data for debugging
    print("Filtered Spendings Data: ", df_filtered)

    # Convert Date to 'YYYY-MM-DD' format and Balance to currency format
    df_filtered['Date'] = pd.to_datetime(df_filtered['Date']).dt.strftime('%Y-%m-%d')
    df_filtered['Amount'] = df_filtered['Amount'].apply(lambda x: f"${x:,.2f}")  # Format to 2 decimal places with currency symbol

    # Rename columns for JSON response
    df_filtered = df_filtered.rename(columns={
        'Account Name': 'Name',           
        'Date': 'Date',           
        'id': 'Id'                
    })

    json_data = df_filtered[['Id', 'Date', 'Name', 'Description', 'Amount']].to_dict(orient='records')
    return JsonResponse(json_data, safe=False)

def plot_category_monthly_data(request):
    print("Plot Category Monthly Data")
    print("Request: ", request)

    # Check if the request method is GET
    if request.method == 'GET':
        year = request.GET.get('year')
        category = request.GET.get('category')
        print("Plot Category Monthly Data", year, category)
        
        # Get the data
        df = get_category_table_data(request, year, category)

        # Group by Month and sum the Amount
        df_grouped = df.groupby(['Month'])['Amount'].sum().reset_index()

        # Prepare the JSON response for Chart.js
        json_data = {
            'labels': [calendar.month_abbr[i] for i in range(1, 13)],  # Abbreviated month names
            'datasets': [{
                'label': category,  # You might want to add the category label for the dataset
                'data': df_grouped['Amount'].round(2).tolist(),  # Monthly summed amounts
                'backgroundColor': 'rgba(75, 192, 192, 0.4)',  # Example background color
                'borderColor': 'rgba(75, 192, 192, 1)',  # Example border color
                'borderWidth': 1,
            }]
        }

        print("Filtered Data Grouped: ", json_data)
        return JsonResponse(json_data, safe=False)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def get_category_table_data(request, year, category):
    df = get_transaction_data(request.user, context="Spendings")
        
    # Correct filtering with parentheses
    df_filtered = df[(df['Year'] == int(year)) & (df['Category'] == category)] # This needs to be exported to the table data function
    
    return df_filtered

# region Spendings
@login_required
def add_spendings_entry(request):
    if request.method == "POST":
        # Get the form data
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        date = request.POST.get('balance-date')
        category = request.POST.get('category')

        category = Category.objects.get(user=request.user, name=category)
        print("Category Search: ", category, type(category))
        account = request.POST.get('account')
        account_name = CardAccount.objects.get(user=request.user, name=account)

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
        return HttpResponseRedirect(reverse("view_spendings"))
    return HttpResponse("Data Entry Error")

@login_required
def plot_spendings_data(request, verbose=True):
    data_dict = _plot_data(request, context="Spendings", group_by="Account Name", verbose=verbose)
    if verbose:
        print("Data Dict: ", data_dict)
    return data_dict

@login_required
def update_spendings(request):
    if request.method == 'POST':
        try:
            # Decode the JSON body from the request
            data = json.loads(request.body.decode('utf-8'))

            for transaction_data in data:
                # Extract the fields for each transaction
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

# region Earnings
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
    return _plot_data(request, context="Earnings", group_by="Description", verbose=verbose)

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


# region Plotting
@login_required
def _plot_data(request, context, group_by, verbose=False):
    df = get_transaction_data(request.user, context=context)
    if df.empty:
        print("\033[91mviews.py - _plot_data: No data available. Please import data first.\033[0m")
    else:
        datasets = []
        # Split by Year
        year_list = df['Year'].unique()
        for year in year_list:
            df_year = df[df['Year'] == year]
            # Generating Labels (Months)
            labels = [calendar.month_abbr[i] for i in range(1, 13)]
            # Get Unique Account Names
            group_list = df_year[group_by].unique()
            #print("Unique Accounts: ", group_list)
            year_dataset_list = []
            for i in range(len(group_list)):
                df_account = df_year[df_year[group_by] == group_list[i]]
                df_monthly_sum = df_account.groupby('Month')['Amount'].sum().reset_index()
                max_month = df_monthly_sum['Month'].max()
                all_months = pd.DataFrame({'Month': range(1, max_month+1)})
                df_complete = all_months.merge(df_monthly_sum, on='Month', how='left').fillna(0)
                monthly_spending_sum_list = df_complete['Amount'].tolist()

                year_dataset = {
                    "label": group_list[i],  # Dataset label
                    "backgroundColor": color_picker(i)[0],  # Background color
                    "borderColor": color_picker(i)[1],  # Border color
                    "borderWidth": 1,
                    "data": monthly_spending_sum_list
                }
                year_dataset_list.append(year_dataset)
            datasets.append({
                "year": int(year),
                "labels": labels[0:max_month],
                "data": year_dataset_list})
        if verbose:
            print("Plot Data - Datasets: ", datasets)
        return JsonResponse(datasets, safe=False)

# endregion

# region Table Data Routes
@login_required
def get_spendings_data_json(request):
    year = request.GET.get('year')
    label = request.GET.get('label')
    month_str = request.GET.get('month')
    month = month_mapping(month_str)

    print("Year: ", year, "Label: ", label, "Month: ", month)

    # Fetch the transaction data based on the user's context
    df = get_transaction_data(request.user, context="Spendings")

    # Filter data by year, label (description), and month
    df_filtered = df[df['Year'] == int(year)]
    df_filtered = df_filtered[df_filtered['Account Name'] == label]
    df_filtered = df_filtered[df_filtered['Month'] == int(month)]
    
    # Print filtered data for debugging
    print("Filtered Spendings Data: ", df_filtered)

    # Convert Date to 'YYYY-MM-DD' format and Balance to currency format
    df_filtered['Date'] = pd.to_datetime(df_filtered['Date']).dt.strftime('%Y-%m-%d')
    df_filtered['Amount'] = df_filtered['Amount'].apply(lambda x: f"${x:,.2f}")  # Format to 2 decimal places with currency symbol

    # Rename columns for JSON response
    df_filtered = df_filtered.rename(columns={
        'Account Name': 'Name',           
        'Date': 'Date',           
        'id': 'Id'                
    })

    json_data = df_filtered[['Id', 'Date', 'Name', 'Description', 'Category', 'Amount']].to_dict(orient='records')

    # Return JSON response
    return JsonResponse(json_data, safe=False)

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

def get_accounts_data_json(request):
    year = request.GET.get('year')
    label = request.GET.get('label')
    month_str = request.GET.get('month')
    month = month_mapping(month_str)
    print("Year: ", year, "Label: ", label, "Month: ", month)
    accounts_histories = AccountHistory.objects.filter(account__user=request.user)
    
    # Create DataFrame from account history records
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

    print("Filtered Accounts Data: ", df_filtered)
    json_data = df_filtered[['id', 'Date', 'Name', 'Balance']].to_dict(orient='records')
    # json_data = _process_transaction_data(balance_history_df[['id', 'account__name', 'balance_history', 'Year', 'Date']], context="Accounts")

    print("Accounts Data JSON: ", df_filtered)
    return JsonResponse(json_data, safe=False)


    if verbose:
        print("_process_transaction_data Dataframe: \n", df)

    if df.empty:
        return {}
    
    if context == "Spendings":
        df["Description"] = df["Description"].str.slice(0, 20)
        group_by = "Account Name"
    elif context == "Earnings":
        df["Description"] = df["Description"].str.slice(0, 20)
        group_by = "Description"
    elif context == "Accounts":
        group_by = "account__name"

    # Split by Year
    data_by_year = {}
    year_list = df['Year'].unique()
    group_by_list = df[group_by].unique()
    print("Group By List: ", group_by_list)
    for year in year_list:
        df_year = df[df['Year'] == year]
        df_year_grouped = {}
        for group in group_by_list:
            df_year_grouped[group] = df_year[df_year[group_by] == group].to_dict(orient='records')
        data_by_year[int(year)] = df_year_grouped
    
    if verbose:
        print("Data by Year: ", data_by_year)
    return data_by_year

# region Accounts
@login_required
def get_latest_accounts_data(request):
    user_accounts = request.user.account.all()
    json_data = []
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

        # Get account id
        account_id = account.id

        # Get account type
        account_type = account.type

        # Collect the necessary data for each account
        accounts_data = {
            'id': account_id,
            'account': account,
            'type': account_type,
            'balance': latest_balance,
            'date': latest_date,
            'history': list(zip(balance_list, date_list)) 
        }
        json_data.append({
            "account_name": account.name,
            "accounts_data": accounts_data})

    # print("get_latest_accounts_data: ", json_data)
    return json_data

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
                "import_path": card_statements_folder_path,
                "export_path": data_folder_path
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

# region Settings
@login_required
def import_statements_data(request):
    sort_statements()
    compiled_df = compile_statements()
    df = categorize_transactions(compiled_df)
    transaction_df_to_db(df, request.user)
    return HttpResponse("Renamed Statements and added to SQL database")

@login_required
def export_statements_data(request):
    transactions_df = get_transaction_data(request.user, context="Transactions")
    earnings_df = get_transaction_data(request.user, context="Earnings")
    accounts_df = get_accounts_data_monthly_df(request)


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
                "import_path": card_statements_folder_path,
                "export_path": data_folder_path
            })
        
        # Create and save the Card account
        card_account = CardAccount(
            user=request.user,
            name=account_name,
        )
        card_account.save()
        
        return view_settings(request)
    return HttpResponse("Add account error")

@login_required
def get_card_settings_data_json(request):
    card_options = CardAccount.objects.filter(user=request.user).values('id', 'name')
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
            # Decode the JSON body from the request
            data = json.loads(request.body.decode('utf-8'))
            print("update_settings_accounts ", data)
            for account in data:
                # Extract the fields for each transaction
                delete_bool = account.get('delete')
                card_id = account.get('id')
                name = account.get('name').strip()
                account_type = account.get('type')
                balance = account.get('balance')
                date = account.get('date')


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
    category_options = Category.objects.filter(user=request.user).values('id', 'name', 'keywords', 'budget', 'variant')

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
            # Decode the JSON body from the request
            data = json.loads(request.body.decode('utf-8'))
            print("Category Settings Data: ", data)
            for category in data:
                # Extract the fields for each transaction
                delete_bool = category.get('delete')
                category_id = category.get('id')
                category_name = category.get('name').strip()
                category_keywords = category.get('keywords').lower()
                category_budget = category.get('budget')
                category_type = category.get('type')
                # Ensure keywords are in CSV format
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

def one_time_import(request):
    # return HttpResponse("Disabled")
    # print("One time transfer")
    # df = pd.read_excel("viz/static/historic_data/TepSpending.xlsx", sheet_name="Transactions", header=1)
    # print(df.head())
    # # Add accounts to the database
    # accounts = df["Account"].unique()
    # for account in accounts:
    #     account = CardAccount(user=request.user, name=account)
    #     account.save()
    
    # print("Added Accounts: ", accounts)

    # # Add categories to the database
    # cat_df = pd.read_excel("viz/static/historic_data/TepSpending.xlsx", sheet_name="Category", header=1)
    # print(cat_df.head())
    # categories = cat_df["Category"].unique()
    
    # for c in categories:
    #     keywords = []
    #     filtered_df = cat_df[cat_df["Category"] == c]
    #     print(filtered_df)
    #     for index, row in filtered_df.iterrows():
    #         item = row["Description"]
    #         print("Item: ", item)
    #         keywords.append(item)
    #     keywords = ','.join(keywords)

    #     c = Category(user=request.user, name=c, keywords=keywords, budget=500, variant="Non Essential")
    #     c.save()

    # print("Added Categories: ", categories)

    # # Iterate over the rows of the DataFrame
    # for index, row in df.iterrows():
    #     date = row["Date"]
    #     description = row["Description"]
    #     amount = row["Amount"]
    #     category = row["Category"]
    #     account = row["Account"]

    #     print(date, description, amount, category, account)

    #     category = Category.objects.get(user=request.user, name=category)
    #     account_name = CardAccount.objects.get(user=request.user, name=account)

    #     # Create and save the transaction
    #     transaction = Transaction(
    #         user=request.user,
    #         account_name = account_name,
    #         description=description,
    #         category=category,
    #         date=date,
    #         amount=amount,
    #     )
    #     transaction.save()
    # print("Added Transactions")

    # Add Earnings
    # earning_df = pd.read_excel("viz/static/historic_data/TepSpending.xlsx", sheet_name="Income", header=0)

    # for index, row in earning_df.iterrows():
    #     date = row["Date"]
    #     description = row["Description"]
    #     amount = row["Amount"]
    #     account = row["Account"]

    #     account_name = Account.objects.get(user=request.user, name=account)

    #     # Create and save the transaction
    #     transaction = Earning(
    #         user=request.user,
    #         account_name = account_name,
    #         description=description,
    #         date=date,
    #         amount=amount,
    #     )
    #     transaction.save()


    return HttpResponse("Data transfer complete")