# views/auth_views.py
import os
from datetime import datetime

import pytz
from apps.expense.models import Expense
from apps.richtato_user.models import CardAccount, Category, User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from loguru import logger

pst = pytz.timezone("US/Pacific")


def index(request: HttpRequest) -> HttpResponseRedirect:
    if request.user.is_authenticated:
        logger.debug(f"User {request.user} is authenticated.")
        return HttpResponseRedirect(reverse("dashboard"))
    else:
        return HttpResponseRedirect(reverse("welcome"))


def dashboard(request: HttpRequest):
    deploy_stage = os.getenv("DEPLOY_STAGE")
    if deploy_stage and deploy_stage.upper() == "PROD":
        suffix = ""
    else:
        suffix = deploy_stage
    return render(request, "dashboard.html", {"suffix": suffix})


def welcome(request: HttpRequest):
    return render(request, "welcome.html")


@login_required
def get_user_id(request: HttpRequest):
    return JsonResponse({"userID": request.user.pk})


def friends(request: HttpRequest):
    return render(request, "friends.html")


def files(request: HttpRequest):
    return render(request, "files.html")


def goals(request: HttpRequest):
    return render(request, "goals.html")


def profile(request: HttpRequest):
    return render(request, "profile.html")


def input(request: HttpRequest):
    spending_dates = (
        Expense.objects.filter(user=request.user)
        .exclude(date__isnull=True)
        .values_list("date", flat=True)
        .distinct()
    )
    years_list = sorted(set(date.year for date in spending_dates), reverse=True)
    transaction_accounts = (
        CardAccount.objects.filter(user=request.user)
        .values_list("name", flat=True)
        .distinct()
    )
    category_list = [""] + list(
        Category.objects.filter(user=request.user).values_list("name", flat=True)
    )

    return render(
        request,
        "input.html",
        {
            "years": years_list,
            "transaction_accounts": transaction_accounts,
            "category_list": category_list,
            "today_date": datetime.now(pst).strftime("%Y-%m-%d"),
            "deploy_stage": os.getenv("DEPLOY_STAGE"),
        },
    )


def user_settings(request: HttpRequest):
    return render(request, "user_settings.html")


def account_settings(request: HttpRequest):
    return render(request, "account_settings.html")


class LoginView(View):
    def get(self, request: HttpRequest):
        return render(
            request,
            "login.html",
            {
                "username": "",
                "message": None,
                "deploy_stage": os.getenv("DEPLOY_STAGE"),
            },
        )

    def post(self, request: HttpRequest):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "login.html",
                {
                    "username": username,
                    "message": "Invalid username and/or password.",
                    "deploy_stage": os.getenv("DEPLOY_STAGE"),
                },
            )


class LogoutView(View):
    def get(self, request: HttpRequest):
        logout(request)
        return HttpResponseRedirect(reverse("index"))


class RegisterView(View):
    def get(self, request: HttpRequest):
        return render(
            request, "register.html", {"deploy_stage": os.getenv("DEPLOY_STAGE")}
        )

    def post(self, request: HttpRequest):
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirmation = request.POST.get("password2")

        if password != confirmation:
            return render(
                request,
                "register.html",
                {
                    "message": "Passwords must match.",
                    "deploy_stage": os.getenv("DEPLOY_STAGE"),
                },
            )

        try:
            user = User.objects.create_user(username=username, password=password)
            user.save()

        except IntegrityError:
            return render(
                request, "register.html", {"message": "Username already taken."}
            )

        login(request, user)
        return HttpResponseRedirect(reverse("index"))
