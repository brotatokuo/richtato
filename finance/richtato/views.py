# Richtato/views.py
from django.shortcuts import render
from django.http import JsonResponse
import random, pandas as pd
import os, calendar
from django.http import HttpResponse
from .utils import *
data_folder_path = r"C:\Users\Alan\OneDrive\Desktop\Richtato\finance\richtato\static\data"
card_statements_folder_path = r"C:\Users\Alan\OneDrive\Desktop\Richtato\finance\richtato\static\data\Credit Card Statements"
file_name = "master_creditcard_data.xlsx"
data_file_path = os.path.join(data_folder_path, file_name)

def chart_view(request):
    return render(request, 'chart.html')

def index(request):
    return render(request, 'chart.html')

def spendings(request):
    return render(request, 'chart.html')

def earnings(request):
    return render(request, 'chart.html')

def accounts(request):
    return render(request, 'chart.html')

def login(request):
    return render(request, 'chart.html')

def register(request):
    return render(request, 'chart.html')

def color_picker(i):
    # Preset colors
    colors = [
    "152,204,44",    # Green
    "255,99,132",    # Red
    "54,162,235",    # Blue
    "255,159,64",    # Orange
    "153,102,255",   # Purple
    "255,206,86",    # Yellow
    "75,192,192",    # Teal
    "255,99,177",    # Pink
    "0,255,255",     # Cyan
    "54,54,235"      # Dark Blue
]
    
    if i+1 > len(colors):
        color = "0,0,0" #black
    else:
        color = colors[i]

    background_color = f"rgba({color}, 0.4)"
    border_color = f"rgba({color}, 1)"
    return background_color, border_color

def master_data(request):
    df = pd.read_excel(data_file_path, header=0)

    # Generating Labels (Months)
    labels = [calendar.month_abbr[i] for i in range(1, 13)]

    # Get Unique Account Names
    accounts_list = df['Account Name'].unique()

    datasets = []
    max_month = 0

    for i in range(len(accounts_list)):
        df_account = df[df["Account Name"] == accounts_list[i]].copy()

        print(df_account.head())

        monthly_sum = df_account.groupby('Month')['Amount'].sum().reset_index()
        monthly_amount = monthly_sum['Amount'].tolist()
        

        if not monthly_sum.empty:
            last_month = monthly_sum['Month'].max()
            max_month = max(max_month, last_month)

            first_month = monthly_sum['Month'].min()
            monthly_amount_list = [0]*max_month
            monthly_amount_list[first_month-1 : first_month-1+len(monthly_amount)] = monthly_amount


        dataset = {
            "label": accounts_list[i],  # Dataset label
            "backgroundColor": color_picker(i)[0],  # Background color
            "borderColor": color_picker(i)[1],  # Border color
            "borderWidth": 1,
            "data": monthly_amount_list
        }
        datasets.append(dataset)

    # Structure the final response
    response_data = {
        "labels": labels[0:max_month],
        "datasets": datasets
    }

    return JsonResponse(response_data, safe=False)

def filter_data_view(request, account, month):
    # Read the Excel file
    df = pd.read_excel(data_file_path, header=0)

    # Filter based on account, month
    filtered_df = df[(df['Account Name'] == account) & (df['Month'] == month)]
    
def organize_statements(request):
    sort_statements()
    compile_statements()
    return HttpResponse("Renamed Statements")