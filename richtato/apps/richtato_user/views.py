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
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
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
from richtato.apps.income.models import Income
from richtato.apps.richtato_user.models import (
    CardAccount,
    Category,
    User,
    supported_card_banks,
)
from richtato.apps.richtato_user.serializers import CategorySerializer
from richtato.apps.richtato_user.utils import (
    _get_line_graph_data_by_month,
    generate_dashboard_context,
)

pst = pytz.timezone("US/Pacific")


# Main view function
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "welcome.html")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    context = generate_dashboard_context(request)
    return render(request, "dashboard.html", context)


@login_required
def get_user_id(request: HttpRequest):
    return JsonResponse({"userID": request.user.pk})


@login_required
def assets(request: HttpRequest):
    logger.debug(f"User {request.user} is authenticated.")
    assets = Account.objects.filter(user=request.user)
    logger.debug(f"Assets for user {request.user}: {assets}")
    return render(request, "assets.html", {"assets": assets})


@login_required
def upload(request: HttpRequest):
    return render(request, "upload.html")


@login_required
def profile(request: HttpRequest):
    return render(request, "profile.html")


@login_required
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


@login_required
def user_settings(request: HttpRequest):
    return render(request, "user_settings.html")


@login_required
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


@login_required
def table(request: HttpRequest):
    return render(request, "table.html")


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
            return HttpResponseRedirect(reverse("dashboard"))
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
        is_demo=True,
        demo_expires_at=timezone.now() + timedelta(hours=1),
        # add other fields as needed
    )
    demo_user.set_unusable_password()
    demo_user.save()

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
        # update category FK - use existing category if available
        if budget.category:
            existing_category = Category.objects.filter(
                user=demo_user, name=budget.category.name
            ).first()
            if existing_category:
                budget.category = existing_category
        budget.save()

    # Clone Expenses
    for expense in Expense.objects.filter(user=template_user):
        expense.pk = None
        expense.user = demo_user
        # update FKs
        if expense.account_name_id in cardaccount_map:
            expense.account_name = cardaccount_map[expense.account_name_id]
        if expense.category:
            existing_category = Category.objects.filter(
                user=demo_user, name=expense.category.name
            ).first()
            if existing_category:
                expense.category = existing_category
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
