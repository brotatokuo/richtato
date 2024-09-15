# Richtato/views.py
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.db import IntegrityError
from django.http import JsonResponse
import random, pandas as pd
import os, calendar
from viz.models import Category, Transaction
from django.http import HttpResponse
from viz.utils import *

from django.contrib.auth import get_user_model
User = get_user_model() 

data_folder_path = os.path.join(parent_path, "static/data")
card_statements_folder_path = os.path.join(data_folder_path, "Credit Card Statements")
file_name = "master_creditcard_data.xlsx"
data_file_path = os.path.join(data_folder_path, file_name)

def index(request):
    return render(request, 'index.html')

def spendings(request):
    return render(request, 'chart.html')

def earnings(request):
    return render(request, 'chart.html')

def accounts(request):
    return render(request, 'chart.html')

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

def import_statements_data(request):
    sort_statements()
    compiled_df = compile_statements()
    df = categorize_transactions(compiled_df)
    post_to_sql(df, request.user)
    return HttpResponse("Renamed Statements and added to SQL database")

def get_sql_data_json(request):
    df = get_sql_data()
    df_json = df.to_dict(orient='records')  # JSON format
    return JsonResponse(df_json, safe=False)

def plot_data(request):
    df = get_sql_data()
    print("Plot Data: ", df.head())
    if df.empty:
        print("\033[91mviews.py - plot_data: No data available. Please import data first.\033[0m")
    else:
        # Generating Labels (Months)
        labels = [calendar.month_abbr[i] for i in range(1, 13)]

        # Get Unique Account Names
        accounts_list = df['Account Name'].unique()
        print("Unique Accounts: ", accounts_list)

        datasets = []
        max_month = 0

        for i in range(len(accounts_list)):
            df_account = df[df["Account Name"] == accounts_list[i]].copy()

            # print(df_account.head())

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
        

