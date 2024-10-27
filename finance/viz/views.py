# Richtato/views.py
import os

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from django.db import IntegrityError

from viz.models import User
from viz.utils import *


data_folder_path = os.path.join(parent_path, "static/data")
card_statements_folder_path = os.path.join(data_folder_path, "Credit Card Statements")
file_name = "master_creditcard_data.xlsx"
data_file_path = os.path.join(data_folder_path, file_name)

def view_index(request):
    return render(request, 'index.html')

def view_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

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
        password = request.POST["password"]
        confirmation = request.POST["password2"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })
        else:
            print("Passwords match")

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
