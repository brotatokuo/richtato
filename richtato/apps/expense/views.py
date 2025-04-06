import json
from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from google_gemini.ai import AI
from loguru import logger

from richtato.apps.expense.models import Expense
from richtato.apps.richtato_user.models import CardAccount, Category, User
from richtato.apps.richtato_user.utils import _get_line_graph_data
from richtato.categories.categories_manager import CategoriesManager
from richtato.statement_imports.cards.card_factory import CardStatement
from richtato.utilities.tools import format_currency, format_date

pst = pytz.timezone("US/Pacific")


@login_required
def main(request):
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
        "expense.html",
        {
            "years": years_list,
            "transaction_accounts": transaction_accounts,
            "category_list": category_list,
            "today_date": datetime.now(pst).strftime("%Y-%m-%d"),
        },
    )


@login_required
def add_entry(request):
    if request.method == "POST":
        description = request.POST.get("description")
        amount = request.POST.get("amount")
        date = request.POST.get("date")
        category = request.POST.get("category")

        category = Category.objects.get(user=request.user, name=category)
        account = request.POST.get("account")
        account_name = CardAccount.objects.get(user=request.user, name=account)

        transaction = Expense(
            user=request.user,
            account_name=account_name,
            description=description,
            category=category,
            date=date,
            amount=amount,
        )
        transaction.save()
        return HttpResponseRedirect(reverse("input"))
    return HttpResponse("Data Entry Error")


@login_required
def update(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    try:
        data = json.loads(request.body.decode("utf-8"))

        for transaction_data in data:
            account_name = transaction_data.get("card")
            delete_bool = transaction_data.get("delete")
            transaction_id = transaction_data.get("id")
            description = transaction_data.get("description")
            date = transaction_data.get("date")
            amount = float(
                transaction_data.get("amount", "").replace("$", "").replace(",", "")
            )
            category_name = transaction_data.get("category", None)

            if delete_bool:
                _delete_expense(transaction_id)
                continue

            category = _get_category(request.user, category_name, transaction_id)
            account = _get_account(request.user, account_name)

            _update_or_create_expense(
                transaction_id,
                request.user,
                date,
                description,
                amount,
                category,
                account,
            )

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def get_recent_entries(request):
    """
    Get the most recent expenses for the user.
    """
    recent_expenses = Expense.objects.filter(user=request.user).order_by("-date")[:5]
    recent_expenses_data = [
        {
            "id": expense.id,
            "date": format_date(expense.date),
            "card": expense.account_name.name,
            "description": expense.description,
            "amount": format_currency(expense.amount),
            "category": expense.category.name,
        }
        for expense in recent_expenses
    ]
    return JsonResponse(recent_expenses_data, safe=False)


def get_line_graph_data(request):
    chart_data = _get_line_graph_data(request.user, Expense, 5)
    months = chart_data["labels"]
    values = chart_data["values"]
    datasets = [
        {
            "label": "Expense",
            "data": values,
            "backgroundColor": "rgba(232, 82, 63, 0.2)",
            "borderColor": "rgba(232, 82, 63, 1)",
            "borderWidth": 1,
        }
    ]
    return JsonResponse({"labels": months, "datasets": datasets})


def get_last_30_days_expense_sum(user: User) -> float:
    today = datetime.now(pst).date()
    thirty_days_ago = today - relativedelta(days=30)
    total_expenses = Expense.objects.filter(
        user=user, date__gte=thirty_days_ago
    ).aggregate(total_amount=Sum("amount"))
    total_sum = total_expenses["total_amount"] or 0  # Use 0 if there's no result
    return total_sum


def get_last_30_days(request):
    """
    Get the cumulative expenses for the last 30 days.
    """
    today = datetime.now(pst).date()
    thirty_days_ago = today - relativedelta(days=30)
    daily_expenses = {today - timedelta(days=i): 0 for i in range(30)}
    expenses = (
        Expense.objects.filter(user=request.user, date__gte=thirty_days_ago)
        .values("date")
        .annotate(total_amount=Sum("amount"))
    )

    # Populate daily expenses with actual expense values
    for expense in expenses:
        expense_date = expense["date"]
        daily_expenses[expense_date] = expense["total_amount"]

    # Generate cumulative sum for each day
    cumulative_expenses = []
    running_total = 0

    for date, expense in sorted(daily_expenses.items()):
        running_total += expense
        cumulative_expenses.append(running_total)
    labels = list(range(1, len(cumulative_expenses) + 1))
    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": "Expenses By Day",
                "data": cumulative_expenses,
                "borderColor": "rgba(232, 82, 63, 1)",
            }
        ],
    }
    return JsonResponse(chart_data)


def _get_table_data(user: User, page: int = 1, page_size: int = 15) -> list:
    table_data = []
    offset = (page - 1) * page_size

    # Fetch only the required slice of data for the current page
    expenses = Expense.objects.filter(
        user=user,
    ).order_by("-date")[offset : offset + page_size]

    for expense in expenses:
        table_data.append(
            {
                "id": expense.id,
                "date": format_date(expense.date),
                "card": expense.account_name.name,
                "description": expense.description,
                "amount": format_currency(expense.amount),
                "category": expense.category.name,
            }
        )

    return table_data


def _get_data_table_expense(user: User) -> JsonResponse:
    expenses = (
        Expense.objects.filter(user=user)
        .order_by("-date")
        .values(
            "id",
            "date",
            "description",
            "amount",
            "account_name__name",
            "category__name",
        )
    )

    # Format the result efficiently
    data = [
        {
            "id": e["id"],
            "date": format_date(e["date"]),
            "card": e["account_name__name"],
            "description": e["description"],
            "amount": format_currency(e["amount"]),
            "category": e["category__name"],
        }
        for e in expenses
    ]

    columns = [
        {"title": "ID", "data": "id"},
        {"title": "Date", "data": "date"},
        {"title": "Card", "data": "card"},
        {"title": "Description", "data": "description"},
        {"title": "Amount", "data": "amount"},
        {"title": "Category", "data": "category"},
    ]

    return JsonResponse({"columns": columns, "data": data})


def _delete_expense(transaction_id):
    try:
        Expense.objects.get(id=transaction_id).delete()
    except Expense.DoesNotExist:
        raise ValueError(f"Transaction with ID '{transaction_id}' does not exist.")


def _get_category(user, category_name, transaction_id):
    if category_name:
        try:
            return Category.objects.get(user=user, name=category_name)
        except Category.DoesNotExist:
            raise ValueError(f"Category '{category_name}' does not exist for the user.")
    else:
        return Expense.objects.get(id=transaction_id).category


def _get_account(user, account_name):
    try:
        return CardAccount.objects.get(user=user, name=account_name)
    except CardAccount.DoesNotExist:
        raise ValueError(f"Account '{account_name}' does not exist for the user.")


def _update_or_create_expense(
    transaction_id, user, date, description, amount, category, account
):
    Expense.objects.update_or_create(
        user=user,
        id=transaction_id,
        defaults={
            "date": date,
            "description": description,
            "amount": amount,
            "category": category,
            "account_name": account,
        },
    )


def guess_category(request):
    """
    Guess the category of an expense based on the description.
    """
    description = request.GET.get("description", "").lower().strip()

    if not description:
        return JsonResponse({"category": ""})

    category = CategoriesManager().search(description)
    logger.debug(f"Category found: {category}")
    try:
        category = category or AI().categorize_transaction(request.user, description)
    except Exception:
        category = ""
    return JsonResponse({"category": category})


def get_full_table_data(request):
    year = request.GET.get("year")
    month = request.GET.get("month")

    table_data = []
    expenses = Expense.objects.filter(
        user=request.user, date__year=year, date__month=month
    )
    for expense in expenses:
        table_data.append(
            {
                "id": expense.id,
                "date": format_date(expense.date),
                "description": expense.description,
                "amount": format_currency(expense.amount),
                "category": expense.category.name,
            }
        )
    return JsonResponse(table_data, safe=False)


def upload_card_statements(request):
    if request.method == "POST":
        logger.debug("Uploading card statements")

        files = request.FILES.getlist("files")
        card_banks = request.POST.getlist("card_banks")
        card_names = request.POST.getlist("card_names")

        if not files:
            logger.warning("No files received in the request.")
            return JsonResponse({"error": "No files received"}, status=400)

        if len(files) != len(card_banks):
            logger.warning(
                f"Mismatch between files ({len(files)}) and card accounts ({len(card_banks)})"
            )
            return JsonResponse(
                {"error": "Mismatch between files and card accounts"}, status=400
            )

        logger.debug(f"Files uploaded: {[file.name for file in files]}")
        logger.debug(f"Card banks selected: {card_banks}")
        logger.debug(f"Card names: {card_names}")

        for file, card_bank, card_name in zip(files, card_banks, card_names):
            card_statement = CardStatement.create_from_file(
                request.user, card_bank, card_name, file.file
            )
            print(card_statement.formatted_df.head())
            card_statement.process()

        return JsonResponse({"message": "Files uploaded successfully"}, status=200)

    return JsonResponse({"error": "Invalid request"}, status=400)
