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
from utilities.tools import month_mapping, color_picker


@login_required
def main(request) -> HttpResponse:
    """
    Budget view that renders the budget.html template
    """
    expense_dates = Expense.objects.filter(user=request.user).exclude(date__isnull=True).values_list('date', flat=True).distinct()
    years_list = sorted(list(set([date.year for date in expense_dates])), reverse=True)
    months_list = [calendar.month_abbr[i] for i in range(1, 13)]
    print(years_list, months_list)
    category_list = sorted(list(Category.objects.filter(user=request.user).values_list('name', flat=True)))

    return render(request, 'budget.html',
                  {"years": years_list,
                   "months": months_list,
                   "categories": category_list
                   })

# @login_required
# def get_budget_months(request):
#     year = request.GET.get('year')

#     months = sorted(list(Expense.objects.filter(user=request.user, date__year=year).dates('date', 'month').values_list('date__month', flat=True)), reverse=True)
#     print("Months: ", months)
#     return JsonResponse(months, safe=False)

@login_required
def get_plot_data(request, year, month):
    category_list = Category.objects.filter(user=request.user)

    month_number = month_mapping(month)

    expense_for_month = Expense.objects.filter(
        user=request.user, 
        date__year=year, 
        date__month=month_number
    ).values('date__month', 'category__name').annotate(total_amount=Sum('amount'))
    
    datasets = []
    for index, category in enumerate(category_list):
        # Find the corresponding expense entry for this category
        expense = next(
            (exp for exp in expense_for_month if exp['category__name'] == category.name),
            None
        )

        # Get the total amount spent for this category in the month
        total_amount = expense['total_amount'] if expense else 0
        
        # Append the data for this category to the dataset
        background_color, border_color = color_picker(index)
        datasets.append({
            'label': category.name,
            'data': [float(total_amount)],
            'backgroundColor': background_color,
            'borderColor': border_color,
            'borderWidth': 1
        })
    print("Expense for Month: ", expense_for_month)
    return JsonResponse(None, safe=False)

@login_required
def get_budget_data_json(request):
    print("Get Budget Table Data")
    year = request.GET.get('year')
    label = request.GET.get('label')
    month = request.GET.get('month')

    print("Year: ", year, "Label: ", label, "Month: ", month)
    # df = get_transaction_data(request.user, context="Spendings")
    df = None
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
    # df = get_transaction_data(request.user, context="Spendings")
    df = None
        
    # Correct filtering with parentheses
    df_filtered = df[(df['Year'] == int(year)) & (df['Category'] == category)] # This needs to be exported to the table data function
    
    return df_filtered         
 