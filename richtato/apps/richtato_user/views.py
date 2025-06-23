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
from richtato.apps.expense.utils import (
    convert_plotly_fig_to_html,
    sankey_by_account,
    sankey_by_category,
)
from richtato.apps.income.models import Income
from richtato.apps.richtato_user.models import (
    CardAccount,
    Category,
    User,
    supported_card_banks,
)
from richtato.apps.richtato_user.serializers import CategorySerializer
from richtato.apps.richtato_user.utils import _get_line_graph_data_by_month
from richtato.utilities.postgres.pg_client import PostgresClient
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


def assets(request: HttpRequest):
    logger.debug(f"User {request.user} is authenticated.")
    assets = Account.objects.filter(user=request.user)
    logger.debug(f"Assets for user {request.user}: {assets}")
    return render(request, "assets.html", {"assets": assets})


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


def timeseries_graph(request: HttpRequest):
    pg_client = PostgresClient()
    expense_df = pg_client.get_expense_df(request.user.pk)
    sankey_by_account_fig = sankey_by_account(expense_df)
    sankey_by_account_html = convert_plotly_fig_to_html(sankey_by_account_fig)
    sankey_by_category_fig = sankey_by_category(expense_df)
    sankey_by_category_html = convert_plotly_fig_to_html(sankey_by_category_fig)
    return render(
        request,
        "graph.html",
        {
            "sankey_by_account": sankey_by_account_html,
            "sankey_by_category": sankey_by_category_html,
        },
    )


class CardBanksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        card_accounts = CardAccount.objects.filter(user=request.user)
        logger.debug(f"User card accounts: {card_accounts}")
        return Response(card_accounts)


class CombinedGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expense_data = _get_line_graph_data_by_month(request.user, Expense)
        logger.debug(f"Expense data: {expense_data}")

        income_data = _get_line_graph_data_by_month(request.user, Income)
        logger.debug(f"Income data: {income_data}")

        chart_data = {
            "labels": expense_data["labels"],  # assumes income labels match
            "datasets": [
                {
                    "label": "Expenses",
                    "data": expense_data["values"],
                    "backgroundColor": "rgba(232, 82, 63, 0.2)",
                    "borderColor": "rgba(232, 82, 63, 0.5)",
                    "borderWidth": 1,
                    "fill": True,
                    "tension": 0.4,
                },
                {
                    "label": "Income",
                    "data": income_data["values"],
                    "backgroundColor": "rgba(152, 204, 44, 0.2)",
                    "borderColor": "rgba(152, 204, 44, 0.5)",
                    "borderWidth": 1,
                    "fill": True,
                    "tension": 0.4,
                },
            ],
        }

        logger.debug(f"Combined chart data: {chart_data}")
        return Response(chart_data)


class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        categories = Category.objects.filter(user=request.user).values()
        rows = []
        for category in categories:
            rows.append(
                {
                    **category,
                    "name": category["name"],
                    "type": category["type"],
                    "budget": format_currency(category["budget"]),
                }
            )
        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "name", "title": "Name"},
                {"field": "type", "title": "Type"},
                {"field": "budget", "title": "Budget"},
            ],
            "rows": rows,
        }
        return Response(data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        else:
            logger.error(f"Category creation error: {serializer.errors}")
            return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        try:
            category = Category.objects.get(pk=pk, user=request.user)
        except Category.DoesNotExist:
            return Response({"error": "Category not found."}, status=404)

        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            logger.error(f"Category update error: {serializer.errors}")
            return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            category = Category.objects.get(pk=pk, user=request.user)
            category.delete()
            return Response(status=204)
        except Category.DoesNotExist:
            return Response({"error": "Category not found."}, status=404)


class CategoryFieldChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "name": [
                {"value": value, "label": label}
                for value, label in Category.supported_categories
            ],
            "type": [
                {"value": value, "label": label}
                for value, label in Category.CATEGORY_TYPES
            ],
        }
        return Response(data)


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
