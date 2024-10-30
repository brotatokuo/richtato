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
from urllib.parse import unquote

@login_required
def view_budget(request):
    spending_dates = Transaction.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
    years_list = sorted(set(date.year for date in spending_dates), reverse=True)
    months_list = sorted(set(date.month for date in spending_dates), reverse=True)
    category_list = sorted(list(Category.objects.filter(user=request.user).values_list('name', flat=True)))

    print("Budget Years: ", years_list)
    print("Budget Months: ", months_list)
    return render(request, 'budget.html',
                  {"years": years_list,
                   "months": months_list,
                   "categories": category_list
                   })

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
                category_color = Category.objects.get(user=request.user, name=category).color
                data_placeholder = [0] * len(categories)
                data_placeholder[index] = category_budget_percent
                category_percentages_datapoint = {
                    'label': category,
                    'backgroundColor':category_color,
                    'borderColor': category_color,
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
        # Get color from the category
        category_obj = Category.objects.get(user=request.user, name=category)
        color = category_obj.color
        print("Category Color: ", color)
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