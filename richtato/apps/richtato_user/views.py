# views/auth_views.py
import os
from datetime import datetime

import pytz
from apps.account.models import Account
from apps.budget.views import get_budget_rankings
from apps.expense.views import get_last_30_days_expense_sum
from apps.income.views import get_last_30_days_income_sum
from apps.richtato_user.models import CardAccount, Category, User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from loguru import logger
from utilities.tools import format_currency

pst = pytz.timezone("US/Pacific")


def calculate_budget_diff(budget, spent):
    diff = budget - spent
    if diff > 0:
        return f"{format_currency(diff)} left"
    else:
        return f"+{format_currency(-diff)} over"


def prepare_category_data(budget_rankings):
    category_data = []
    for ranking in budget_rankings:
        spent = ranking["expense_this_month"]
        diff = calculate_budget_diff(ranking["budget"], spent)

        category_info = {
            "name": ranking["category_name"],
            "budget": format_currency(ranking["budget"]),
            "spent": format_currency(spent),
            "diff": diff,
        }
        category_data.append(category_info)
    return category_data


# Main view function
def index(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    if request.user.is_authenticated:
        logger.debug(f"User {request.user} is authenticated.")

        networth = request.user.networth()
        expense_sum = get_last_30_days_expense_sum(request.user)
        income_sum = get_last_30_days_income_sum(request.user)
        budget_rankings = get_budget_rankings(request.user)


        category_data = prepare_category_data(budget_rankings)
        context = {
            "networth": format_currency(networth),
            "expense_sum": format_currency(expense_sum),
            "income_sum": format_currency(income_sum),
            "categories": category_data,  # List of category data
        }

        # Render the response with the context
        return render(request, "dashboard.html", context)

    else:
        return HttpResponseRedirect(reverse("welcome"))


def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard.html", {"user_tier": "Alpha User"})


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
    transaction_accounts = (
        CardAccount.objects.filter(user=request.user)
        .values_list("name", flat=True)
        .distinct()
    )
    category_list = [""] + list(
        Category.objects.filter(user=request.user).values_list("name", flat=True)
    )

    account_names = list(Account.objects.filter(user=request.user))

    return render(
        request,
        "input.html",
        {
            "transaction_accounts": transaction_accounts,
            "category_list": category_list,
            "today_date": datetime.now(pst).strftime("%Y-%m-%d"),
            "bank_accounts": account_names,
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
