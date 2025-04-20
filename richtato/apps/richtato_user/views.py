# views/auth_views.py
import os
from datetime import datetime

import pytz
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from loguru import logger
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from richtato.apps.account.models import (
    Account,
    account_types,
    supported_asset_accounts,
)
from richtato.apps.expense.models import Expense
from richtato.apps.income.models import Income
from richtato.apps.richtato_user.models import (
    CardAccount,
    Category,
    User,
    supported_card_banks,
)
from richtato.apps.richtato_user.utils import _get_line_graph_data
from richtato.utilities.tools import format_currency

pst = pytz.timezone("US/Pacific")


# Main view function
def index(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    if request.user.is_authenticated:
        logger.debug(f"User {request.user} is authenticated.")
        accounts = Account.objects.filter(user=request.user)
        networth = (
            sum(account.latest_balance for account in accounts) if accounts else 0.0
        )
        expense_sum = 0
        income_sum = 0
        savings_rate = (
            round((income_sum - expense_sum) / income_sum * 100) if income_sum else 0
        )
        context = {
            "networth": format_currency(networth),
            "expense_sum": format_currency(expense_sum),
            "income_sum": format_currency(income_sum),
            "savings_rate": f"{savings_rate}%",
        }

        # Render the response with the context
        return render(request, "dashboard.html", context)

    else:
        return render(request, "welcome.html")


def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard.html", {"user_tier": "Alpha User"})


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
    return render(
        request,
        "account_settings.html",
        {
            "supported_card_banks": supported_card_banks,
            "supported_asset_accounts": supported_asset_accounts,
            "supported_asset_types": account_types,
        },
    )


def table(request: HttpRequest):
    return render(request, "table.html")


def get_table_data(request: HttpRequest):
    table_option = request.GET.get("option")
    limit = request.GET.get("limit")
    if limit:
        limit = int(limit)
    logger.debug(f"Table option: {table_option}, limit: {limit}")
    table_data_getters = {
        "expense": 0,
        "income": 0,
    }

    if table_option in table_data_getters:
        logger.debug(f"Getting table data for {table_option}.")
        return table_data_getters[table_option](request.user, limit)
    else:
        logger.error(f"Invalid table option: {table_option}")
        return JsonResponse({"error": "Invalid table option."}, status=400)


def timeseries_plots(request: HttpRequest):
    return render(request, "timeseries_plots.html")


def get_timeseries_data(request: HttpRequest) -> JsonResponse:
    month_range = request.GET.get("month_range")
    month_range = int(month_range) if month_range else None
    expense_data = _get_line_graph_data(request.user, Expense, month_range)
    logger.debug(f"Expense data: {expense_data}")
    income_data = _get_line_graph_data(request.user, Income, month_range)
    logger.debug(f"Income data: {income_data}")

    chart_data = {
        "labels": expense_data["labels"],
        "datasets": [
            {
                "label": "Expenses",
                "data": expense_data["values"],
                "borderColor": "rgba(232, 82, 63, 0.5)",
                "fill": True,
                "tension": 0.4,
            },
            {
                "label": "Income",
                "data": income_data["values"],
                "borderColor": "rgba(152, 204, 44, 0.5)",
                "fill": True,
                "tension": 0.4,
            },
        ],
    }
    logger.debug(f"Chart data: {chart_data}")

    return JsonResponse(chart_data)


def get_card_banks(request: HttpRequest) -> JsonResponse:
    cards = CardAccount.objects.filter(user=request.user).values("name", "card_bank")
    logger.debug(f"Cards: {cards}")
    cards_dict = {
        "cards": [
            {
                "value": card["card_bank"],
                "label": card["name"],
            }
            for card in cards
        ]
    }
    return JsonResponse(cards_dict, safe=False)


class CombinedGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        months = request.query_params.get("months")
        months = int(months) if months else None

        expense_data = _get_line_graph_data(request.user, Expense, months)
        logger.debug(f"Expense data: {expense_data}")

        income_data = _get_line_graph_data(request.user, Income, months)
        logger.debug(f"Income data: {income_data}")

        chart_data = {
            "labels": expense_data["labels"],  # assumes income labels match
            "datasets": [
                {
                    "label": "Expenses",
                    "data": expense_data["values"],
                    "backgroundColor": "rgba(232, 82, 63, 0.2)",
                    "borderColor": "rgba(232, 82, 63, 1)",
                    "borderWidth": 1,
                    "fill": True,
                    "tension": 0.4,
                },
                {
                    "label": "Income",
                    "data": income_data["values"],
                    "backgroundColor": "rgba(152, 204, 44, 0.2)",
                    "borderColor": "rgba(152, 204, 44, 1)",
                    "borderWidth": 1,
                    "fill": True,
                    "tension": 0.4,
                },
            ],
        }

        logger.debug(f"Combined chart data: {chart_data}")
        return Response(chart_data)


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
