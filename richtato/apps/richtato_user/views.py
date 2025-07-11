# views/auth_views.py
import os
import random
import string
from datetime import datetime, timedelta

import pytz
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from loguru import logger
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from richtato.apps.account.models import (
    Account,
    AccountTransaction,
    account_types,
    supported_asset_accounts,
)
from richtato.apps.budget.models import Budget
from richtato.apps.expense.models import Expense
from richtato.apps.expense.utils import (
    convert_plotly_fig_to_html,
    sankey_by_account,
    sankey_by_category,
    sankey_cash_flow_overview,
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
            round(sum(account.latest_balance for account in accounts))
            if accounts
            else 0.0
        )

        # Calculate networth growth percentage
        networth_growth = calculate_networth_growth(request.user)
        # Calculate networth growth CSS class
        networth_growth_class = (
            "positive"
            if networth_growth.startswith("+")
            else "negative"
            if networth_growth.startswith("-")
            else ""
        )

        # Calculate total income and total expense
        total_income = (
            Income.objects.filter(user=request.user).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )
        total_expense = (
            Expense.objects.filter(user=request.user).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )
        expense_sum = total_expense
        income_sum = total_income
        if total_income > 0:
            print("Total income: ", total_income)
            print("Total expense: ", total_expense)
            savings_rate = round((total_income - total_expense) / total_income * 100, 1)
        else:
            savings_rate = 0

        # Calculate savings rate context
        savings_rate_str = f"{savings_rate}%"
        savings_rate_context, savings_rate_class = calculate_savings_rate_context(
            savings_rate_str
        )

        # Calculate % of non-essential spending
        nonessential_expense = (
            Expense.objects.filter(
                user=request.user, category__type="nonessential"
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        nonessential_spending_pct = (
            round((nonessential_expense / total_expense) * 100, 1)
            if total_expense > 0
            else 0
        )

        # pg_client = PostgresClient()
        # expense_df = pg_client.get_expense_df(request.user.pk)

        # Create comprehensive cash flow Sankey diagram
        sankey_cash_flow_fig = sankey_cash_flow_overview(request.user.pk)
        sankey_cash_flow_html = convert_plotly_fig_to_html(sankey_cash_flow_fig)

        context = {
            "networth": format_currency(networth, 0),
            "networth_growth": networth_growth,
            "networth_growth_class": networth_growth_class,
            "expense_sum": format_currency(expense_sum),
            "income_sum": format_currency(income_sum),
            "savings_rate": savings_rate_str,
            "savings_rate_context": savings_rate_context,
            "savings_rate_class": savings_rate_class,
            "sankey_cash_flow": sankey_cash_flow_html,
            "nonessential_spending_pct": nonessential_spending_pct,
        }

        # Render the response with the context
        return render(request, "dashboard.html", context)

    else:
        return render(request, "welcome.html")


def calculate_networth_growth(user):
    """
    Calculate networth growth percentage for the current month compared to previous month.
    Returns a formatted string like "+5.2% this month" or "-2.1% this month"
    """
    try:
        # Get current date and calculate previous month
        current_date = datetime.now().date()
        current_month_start = current_date.replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)

        # Get current networth (sum of all account latest balances)
        current_accounts = Account.objects.filter(user=user)
        current_networth = (
            sum(account.latest_balance for account in current_accounts)
            if current_accounts
            else 0
        )

        # Get previous month's networth from account transactions
        previous_networth = 0
        for account in current_accounts:
            # Get the latest transaction for this account before the current month
            latest_transaction = (
                AccountTransaction.objects.filter(
                    account=account, date__lt=current_month_start
                )
                .order_by("-date")
                .first()
            )

            if latest_transaction:
                previous_networth += latest_transaction.amount
            else:
                # If no previous transaction, assume balance was 0
                previous_networth += 0

        # Calculate growth percentage
        if previous_networth > 0:
            growth_percentage = (
                (current_networth - previous_networth) / previous_networth
            ) * 100
            growth_percentage = round(growth_percentage, 1)

            # Format the result
            if growth_percentage >= 0:
                return f"+{growth_percentage}% this month"
            else:
                return f"{growth_percentage}% this month"
        else:
            # If no previous networth data, return a default message
            return "New this month"

    except Exception as e:
        logger.error(f"Error calculating networth growth: {e}")
        return "N/A"


def calculate_savings_rate_context(savings_rate):
    """
    Calculate savings rate context based on percentage ranges.
    Returns a tuple of (context_text, css_class)
    """
    try:
        # Extract the numeric value from savings_rate (remove '%' and convert to float)
        rate_value = float(savings_rate.replace("%", ""))

        if rate_value < 10:
            return "Below average", "negative"
        elif rate_value >= 10 and rate_value <= 20:
            return "Average", ""
        elif rate_value > 30:
            return "Above average", "positive"
        else:
            # Between 20-30%
            return "Good", "positive"

    except (ValueError, AttributeError):
        # If we can't parse the savings rate, return a default
        return "N/A", ""


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


def upload(request: HttpRequest):
    return render(request, "upload.html")


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
        categories = Category.objects.filter(user=request.user)
        rows = []
        for category in categories:
            rows.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "type": category.get_type_display(),
                }
            )
        data = {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "name", "title": "Name"},
                {"field": "type", "title": "Type"},
            ],
            "rows": rows,
        }
        return Response(data)

    def post(self, request):
        data = request.data
        data["budget"] = float(data["budget"].replace("$", ""))
        logger.debug(f"Category creation data: {data}")
        serializer = CategorySerializer(data=data)
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
        data = request.data
        logger.debug(f"Category edit data: {data}")
        serializer = CategorySerializer(category, data=data, partial=True)
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
        email = request.POST.get("email")
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

        # Validate password requirements
        if not self._validate_password(password):
            return render(
                request,
                "register.html",
                {
                    "message": "Password must be at least 8 characters long and contain at least one symbol (!@#$%^&*).",
                },
            )

        try:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            user.save()

        except IntegrityError:
            return render(
                request,
                "register.html",
                {"message": "Username or email already taken."},
            )

        login(request, user)
        return HttpResponseRedirect(reverse("index"))

    def _validate_password(self, password):
        """
        Validate password requirements:
        - At least 8 characters long
        - Contains at least one symbol
        """
        if len(password) < 8:
            return False

        import re

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False

        return True


@csrf_exempt
@require_http_methods(["POST"])
def check_username_availability(request):
    """
    Check if a username is available for registration.
    Returns JSON response with availability status.
    """
    username = request.POST.get("username", "").strip()

    if not username:
        return JsonResponse({"available": False, "message": "Username is required."})

    try:
        User.objects.get(username=username)
        return JsonResponse({"available": False, "message": "Username already taken."})
    except User.DoesNotExist:
        return JsonResponse({"available": True, "message": "Username is available."})
    except Exception:
        return JsonResponse(
            {"available": False, "message": "Error checking username availability."}
        )


def generate_demo_username():
    return "demo_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=8)
    )


@transaction.atomic
def demo_login(request):
    template_user = User.objects.get(username="demo")
    demo_username = generate_demo_username()
    demo_user = User.objects.create(
        username=demo_username,
        # add other fields as needed
    )
    demo_user.set_unusable_password()
    demo_user.save()

    # Clone Categories
    category_map = {}
    for category in Category.objects.filter(user=template_user):
        old_id = category.id
        category.pk = None
        category.user = demo_user
        category.save()
        category_map[old_id] = category

    # Clone Accounts
    account_map = {}
    for account in Account.objects.filter(user=template_user):
        old_id = account.id
        account.pk = None
        account.user = demo_user
        account.save()
        account_map[old_id] = account

    # Clone CardAccounts
    cardaccount_map = {}
    for card in CardAccount.objects.filter(user=template_user):
        old_id = card.id
        card.pk = None
        card.user = demo_user
        card.save()
        cardaccount_map[old_id] = card

    # Clone Budgets
    for budget in Budget.objects.filter(user=template_user):
        budget.pk = None
        budget.user = demo_user
        # update category FK
        if budget.category_id in category_map:
            budget.category = category_map[budget.category_id]
        budget.save()

    # Clone Expenses
    for expense in Expense.objects.filter(user=template_user):
        expense.pk = None
        expense.user = demo_user
        # update FKs
        if expense.account_name_id in cardaccount_map:
            expense.account_name = cardaccount_map[expense.account_name_id]
        if expense.category_id in category_map:
            expense.category = category_map[expense.category_id]
        expense.save()

    # Clone Incomes
    for income in Income.objects.filter(user=template_user):
        income.pk = None
        income.user = demo_user
        if income.account_name_id in account_map:
            income.account_name = account_map[income.account_name_id]
        income.save()

    # Clone AccountTransactions
    for tx in AccountTransaction.objects.filter(account__user=template_user):
        tx.pk = None
        if tx.account_id in account_map:
            tx.account = account_map[tx.account_id]
        tx.save()

    login(request, demo_user)
    request.session["is_demo_user"] = True
    return redirect("index")


class CustomPasswordResetView(PasswordResetView):
    template_name = "password_reset.html"
    email_template_name = "password_reset_email.html"
    subject_template_name = "password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")
