"""Shared constants used across multiple apps."""

from django.db.models import Q

CC_PAYMENT_CATEGORY_SLUG = "credit-card-payment"


def get_expense_filter() -> Q:
    """Q filter for expense transactions, excluding credit-card payments.

    Expense = category.type == "expense" OR uncategorized debit.
    """
    expense_filter = Q(category__type="expense") | Q(category__isnull=True, transaction_type="debit")
    cc_payment_exclusion = ~Q(category__slug=CC_PAYMENT_CATEGORY_SLUG)
    return expense_filter & cc_payment_exclusion


def get_income_filter() -> Q:
    """Q filter for income transactions.

    Income = category.type == "income" OR uncategorized credit.
    """
    return Q(category__type="income") | Q(category__isnull=True, transaction_type="credit")


def get_investment_filter() -> Q:
    """Q filter for investment transactions.

    Investment = category.type == "investment".
    """
    return Q(category__type="investment")
