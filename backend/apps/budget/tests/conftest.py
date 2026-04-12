"""Shared fixtures for budget tests."""

from datetime import date
from decimal import Decimal

import pytest
from apps.budget.models import Budget, BudgetCategory
from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="budgettest", email="budget@test.com", password="testpass123"
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="otheruser", email="other@test.com", password="testpass123"
    )


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Test Checking",
        account_type="checking",
        balance=Decimal("10000.00"),
    )


@pytest.fixture
def expense_category(user):
    return TransactionCategory.objects.create(
        user=user, name="Test Groceries", slug="test-groceries-budget", type="expense"
    )


@pytest.fixture
def expense_category_2(user):
    return TransactionCategory.objects.create(
        user=user, name="Test Transport", slug="test-transport-budget", type="expense"
    )


@pytest.fixture
def income_category(user):
    return TransactionCategory.objects.create(
        user=user, name="Test Salary", slug="test-salary-budget", type="income"
    )


@pytest.fixture
def budget(user):
    return Budget.objects.create(
        user=user,
        name="January 2024",
        period_type="monthly",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )


@pytest.fixture
def budget_category(budget, expense_category):
    return BudgetCategory.objects.create(
        budget=budget,
        category=expense_category,
        allocated_amount=Decimal("500.00"),
    )


@pytest.fixture
def budget_category_with_rollover(budget, expense_category):
    return BudgetCategory.objects.create(
        budget=budget,
        category=expense_category,
        allocated_amount=Decimal("500.00"),
        rollover_enabled=True,
        rollover_amount=Decimal("100.00"),
    )


def create_transaction(user, account, category, amount, txn_date, transaction_type="debit"):
    """Helper to create a transaction without triggering balance signals."""
    return Transaction.objects.create(
        user=user,
        account=account,
        category=category,
        amount=amount,
        date=txn_date,
        description=f"Test {transaction_type} {amount}",
        transaction_type=transaction_type,
        sync_source="manual",
    )
