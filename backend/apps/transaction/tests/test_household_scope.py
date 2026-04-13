"""Tests for transaction repository household scope queries."""

from datetime import date
from decimal import Decimal

import pytest

from apps.financial_account.models import FinancialAccount
from apps.household.models import Household, HouseholdMember
from apps.richtato_user.models import User
from apps.transaction.models import Transaction
from apps.transaction.repositories.transaction_repository import TransactionRepository


@pytest.fixture
def user_a(db):
    return User.objects.create_user(username="txn_a", password="testpass123")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(username="txn_b", password="testpass123")


@pytest.fixture
def household_both(user_a, user_b):
    h = Household.objects.create(name="Test", created_by=user_a)
    HouseholdMember.objects.create(household=h, user=user_a)
    HouseholdMember.objects.create(household=h, user=user_b)
    return h


@pytest.fixture
def shared_account_a(user_a):
    return FinancialAccount.objects.create(
        user=user_a,
        name="A Shared",
        account_type="checking",
        balance=Decimal("1000"),
        shared_with_household=True,
    )


@pytest.fixture
def private_account_b(user_b):
    return FinancialAccount.objects.create(
        user=user_b,
        name="B Private",
        account_type="savings",
        balance=Decimal("500"),
        shared_with_household=False,
    )


@pytest.fixture
def shared_account_b(user_b):
    return FinancialAccount.objects.create(
        user=user_b,
        name="B Shared",
        account_type="checking",
        balance=Decimal("3000"),
        shared_with_household=True,
    )


@pytest.fixture
def repo():
    return TransactionRepository()


def _create_txn(user, account, amount=Decimal("50")):
    return Transaction.objects.create(
        user=user,
        account=account,
        amount=amount,
        date=date(2024, 6, 15),
        description="test",
        transaction_type="debit",
        sync_source="manual",
    )


class TestHouseholdScopeTransactions:
    def test_personal_scope_returns_only_own_transactions(
        self,
        repo,
        user_a,
        user_b,
        shared_account_a,
        shared_account_b,
        household_both,
    ):
        txn_a = _create_txn(user_a, shared_account_a)
        txn_b = _create_txn(user_b, shared_account_b)
        result = list(repo.get_by_user(user_a))
        ids = {t.id for t in result}
        assert txn_a.id in ids
        assert txn_b.id not in ids

    def test_household_scope_returns_transactions_from_shared_accounts(
        self,
        repo,
        user_a,
        user_b,
        shared_account_a,
        shared_account_b,
        household_both,
    ):
        txn_a = _create_txn(user_a, shared_account_a)
        txn_b = _create_txn(user_b, shared_account_b)
        result = list(repo.get_by_user_ids_shared([user_a.id, user_b.id]))
        ids = {t.id for t in result}
        assert txn_a.id in ids
        assert txn_b.id in ids

    def test_household_scope_excludes_transactions_from_unshared_accounts(
        self,
        repo,
        user_a,
        user_b,
        shared_account_a,
        private_account_b,
        household_both,
    ):
        _create_txn(user_a, shared_account_a)
        txn_private = _create_txn(user_b, private_account_b)
        result = list(repo.get_by_user_ids_shared([user_a.id, user_b.id]))
        ids = {t.id for t in result}
        assert txn_private.id not in ids

    def test_household_scope_with_single_user(
        self,
        repo,
        user_a,
        shared_account_a,
    ):
        txn = _create_txn(user_a, shared_account_a)
        result = list(repo.get_by_user_ids_shared([user_a.id]))
        assert txn.id in {t.id for t in result}
