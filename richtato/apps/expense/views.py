import json
from datetime import datetime

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse

from apps.expense.models import Expense
from apps.richtato_user.models import CardAccount, Category, User
from utilities.ai import AI
from django.db.models import Sum
from utilities.tools import month_mapping, color_picker, format_currency, format_date


@login_required
def expense(request):
    if not isinstance(request.user, User):
        print(f"request.user is not a User instance: {request.user}")

    try:
        print("Request User: ", request.user)
        spending_dates = Expense.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
        years_list = sorted(set(date.year for date in spending_dates), reverse=True)
        transaction_accounts = CardAccount.objects.filter(user=request.user).values_list('name', flat=True).distinct()
        category_list = list(Category.objects.filter(user=request.user).values_list('name', flat=True))
        category_list.insert(0, "")

    except Exception as e:
        print(f"Error while querying transactions: {e}")
        years_list = sorted(set(date.year for date in spending_dates)) if spending_dates else []
        transaction_accounts = CardAccount.objects.filter(user=request.user)\
                                                .values_list('name', flat=True)\
                                                .distinct()
        category_list = list(Category.objects.filter(user=request.user).values_list('name', flat=True))

    return render(request, 'expense.html',
                {"years": years_list,
                "transaction_accounts": transaction_accounts,
                "category_list": category_list,
                    "today_date": datetime.today().strftime('%Y-%m-%d')
                })

@login_required
def add_expense_entry(request):
    if request.method == "POST":
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        date = request.POST.get('balance-date')
        category = request.POST.get('category')

        category = Category.objects.get(user=request.user, name=category)
        print("Category Search: ", category, type(category))
        account = request.POST.get('account')
        account_name = CardAccount.objects.get(user=request.user, name=account)

        transaction = Expense(
            user=request.user,
            account_name = account_name,
            description=description,
            category=category,
            date=date,
            amount=amount,
        )
        transaction.save()
        return HttpResponseRedirect(reverse("expense"))
    return HttpResponse("Data Entry Error")

@login_required
def update_expenses(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        data = json.loads(request.body.decode('utf-8'))

        for transaction_data in data:
            print("Transaction Data: ", transaction_data)
            account_name = transaction_data.get('filter')
            delete_bool = transaction_data.get('delete')
            transaction_id = transaction_data.get('id')
            description = transaction_data.get('description')
            date = transaction_data.get('date')
            amount = float(transaction_data.get('amount', '').replace('$', '').replace(',', ''))
            category_name = transaction_data.get('category', None)

            if delete_bool:
                _delete_expense(transaction_id)
                continue

            category = _get_category(request.user, category_name, transaction_id)
            account = _get_account(request.user, account_name)

            _update_or_create_expense(transaction_id, request.user, date, description, amount, category, account)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_expense_plot_data(request, year):
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    cards = CardAccount.objects.filter(user=request.user)
    all_expenses = Expense.objects.filter(user=request.user, date__year=year)
    
    datasets = []
    for card in cards:
        card_expenses = []
        card_name = card.name
        print("Card Name: ", card_name)

        for month in range(1, 13): 
            total_expenses_for_card = all_expenses.filter(account_name=card, date__month=month).aggregate(Sum('amount'))['amount__sum']

            # Handle cases where there are no expenses (None values)
            if total_expenses_for_card is None:
                total_expenses_for_card = 0
            
            card_expenses.append(total_expenses_for_card)

        # Build the dataset for the chart
        dataset = {
            'label': card.name,
            'data': card_expenses,
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1
        }
        datasets.append(dataset)

    print("Datasets: ", datasets)

    return JsonResponse({'labels': month_list, 'datasets': datasets})

def get_expense_table_data(request) -> JsonResponse:
    print("Getting Expense Table Data")
    year = request.GET.get('year', None)
    month = month_mapping(request.GET.get('month', None))
    account = request.GET.get('label', None)
    print(f"Year: {year}, Month: {month}, Account: {account}")

    table_data = []
    if year and month and account:
        expenses = Expense.objects.filter(user=request.user, date__year=year, date__month=month, account_name__name=account)
        for expense in expenses:
            table_data.append({
                'id': expense.id,
                'date': format_date(expense.date),
                'description': expense.description,
                'amount': format_currency(expense.amount),
                'category': expense.category.name
            })
        
        print("Table Data: ", table_data)

    return JsonResponse(table_data, safe=False)
    
def _delete_expense(transaction_id):
    try:
        Expense.objects.get(id=transaction_id).delete()
        print(f"Expense Deleted: {transaction_id}")
    except Expense.DoesNotExist:
        print(f"Expense with ID {transaction_id} does not exist.")

def _get_category(user, category_name, transaction_id):
    if category_name:
        try:
            return Category.objects.get(user=user, name=category_name)
        except Category.DoesNotExist:
            raise ValueError(f"Category '{category_name}' does not exist for the user.")
    else:
        return Expense.objects.get(id=transaction_id).category

def _get_account(user, account_name):
    try:
        return CardAccount.objects.get(user=user, name=account_name)
    except CardAccount.DoesNotExist:
        raise ValueError(f"Account '{account_name}' does not exist for the user.")

def _update_or_create_expense(transaction_id, user, date, description, amount, category, account):
    Expense.objects.update_or_create(
        user=user,
        id=transaction_id,
        defaults={
            'date': date,
            'description': description,
            'amount': amount,
            'category': category,
            'account_name': account
        }
    )
    print(f"Expense Updated: {transaction_id} - {date} {description} {amount} {category.name} {account.name}")
