"""Shared fixtures for household tests."""

from decimal import Decimal

import pytest

from apps.financial_account.models import FinancialAccount
from apps.household.models import Household, HouseholdMember
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory


@pytest.fixture
def user_a(db):
    return User.objects.create_user(username="user_a", password="testpass123")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(username="user_b", password="testpass123")


@pytest.fixture
def user_c(db):
    return User.objects.create_user(username="user_c", password="testpass123")


@pytest.fixture
def household(user_a):
    h = Household.objects.create(name="Test Household", created_by=user_a)
    HouseholdMember.objects.create(household=h, user=user_a)
    return h


@pytest.fixture
def household_with_both(household, user_b):
    HouseholdMember.objects.create(household=household, user=user_b)
    return household


@pytest.fixture
def shared_account_a(user_a):
    return FinancialAccount.objects.create(
        user=user_a,
        name="A Checking",
        account_type="checking",
        balance=Decimal("5000.00"),
        shared_with_household=True,
    )


@pytest.fixture
def private_account_a(user_a):
    return FinancialAccount.objects.create(
        user=user_a,
        name="A Private Savings",
        account_type="savings",
        balance=Decimal("2000.00"),
        shared_with_household=False,
    )


@pytest.fixture
def shared_account_b(user_b):
    return FinancialAccount.objects.create(
        user=user_b,
        name="B Checking",
        account_type="checking",
        balance=Decimal("3000.00"),
        shared_with_household=True,
    )


@pytest.fixture
def private_account_b(user_b):
    return FinancialAccount.objects.create(
        user=user_b,
        name="B Savings",
        account_type="savings",
        balance=Decimal("1000.00"),
        shared_with_household=False,
    )


@pytest.fixture
def category_a(user_a):
    return TransactionCategory.objects.create(
        user=user_a, name="Groceries", slug="groceries", type="expense",
    )


@pytest.fixture
def category_b(user_b):
    return TransactionCategory.objects.create(
        user=user_b, name="Groceries", slug="groceries", type="expense",
    )


@pytest.fixture
def unique_category_a(user_a):
    return TransactionCategory.objects.create(
        user=user_a, name="Pet Supplies", slug="pet-supplies", type="expense",
    )


def create_txn(user, account, amount, txn_date, category=None, txn_type="debit"):
    return Transaction.objects.create(
        user=user,
        account=account,
        category=category,
        amount=amount,
        date=txn_date,
        description=f"Test {txn_type} {amount}",
        transaction_type=txn_type,
        sync_source="manual",
    )
