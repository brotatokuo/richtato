import calendar
import json
import os
from collections import defaultdict
from urllib.parse import unquote

import pandas as pd
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse

from apps.expense.models import Expense
from apps.richtato_user.models import Category, User
from utilities.utils import *


@login_required
def budget(request) -> HttpResponse:
    """
    Budget view that renders the budget.html template
    """
    spending_dates = Expense.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
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

    months = sorted(list(Expense.objects.filter(user=request.user, date__year=year).dates('date', 'month').values_list('date__month', flat=True)), reverse=True)
    print("Months: ", months)
    return JsonResponse(months, safe=False)

@login_required
def plot_budget_data(request):
    # Fetch all transactions in one query, aggregating by year, month, and category
    transactions = (
        Expense.objects
        .filter(user=request.user)
        .exclude(date__isnull=True)
        .values('date__year', 'date__month', 'category__name')
        .annotate(total_amount=Sum('amount'))
    )

    # Fetch all categories in bulk
    categories = Category.objects.filter(user=request.user).values('name', 'budget', 'color')

    # Create a lookup table for category budgets and colors
    category_info = {cat['name']: cat for cat in categories}

    # Initialize the data structure
    data_by_year = defaultdict(lambda: defaultdict(dict))

    print("Data by Year initialized: ", data_by_year)

    # Organize transactions by year, month, and category
    for transaction in transactions:
        year = transaction['date__year']
        month = transaction['date__month']
        category = transaction['category__name']
        total_amount = transaction['total_amount']

        # Get category budget and color
        if category in category_info:
            budget = category_info[category]['budget']
            color = category_info[category]['color']
            budget_percent = round(total_amount * 100 / budget) if budget else 0

            # Add the budget percentage for the category in the correct year and month
            if 'datasets' not in data_by_year[year][month]:
                data_by_year[year][month]['datasets'] = []
                data_by_year[year][month]['labels'] = []

            # Append the label only once
            if category not in data_by_year[year][month]['labels']:
                data_by_year[year][month]['labels'].append(category)
            
            data_placeholder = [0] * len(category_info)
            category_index = data_by_year[year][month]['labels'].index(category)
            data_placeholder[category_index] = budget_percent

            # Prepare the dataset for each category
            data_by_year[year][month]['datasets'].append({
                'label': category,
                'backgroundColor': color,
                'borderColor': color,
                'borderWidth': 1,
                'data': data_placeholder
            })

    # Convert the defaultdict structure to a list
    json_data = []
    for year, months in data_by_year.items():
        month_data = []
        for month, data in months.items():
            month_data.append({
                'month': month,
                'data': {
                    'labels': data['labels'],
                    'datasets': data['datasets']
                }
            })
        json_data.append({
            'year': year,
            'data': month_data
        })

    print("New function JSON Data: ", json_data)
    # Return the JSON response
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
                'backgroundColor': color,
                'borderColor': color,
                'borderWidth': 10,
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
 