"""Tests for Opening Balance transaction on account creation."""

from datetime import date
from decimal import Decimal

import pytest

from apps.financial_account.models import AccountBalanceHistory
from apps.financial_account.services.account_service import AccountService
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


@pytest.fixture
def user(db):
    return User.objects.create_user(username="opentest", email="open@test.com", password="testpass123")


@pytest.fixture
def service():
    return AccountService()


class TestOpeningBalance:
    """Creating an account with initial_balance should create an Opening Balance txn."""

    def test_positive_initial_balance(self, service, user):
        account = service.create_manual_account(
            user=user,
            name="New Checking",
            account_type="checking",
            initial_balance=Decimal("5000.00"),
        )

        account.refresh_from_db()
        assert account.balance == Decimal("5000.00")

        txn = Transaction.objects.get(account=account, description="Opening Balance")
        assert txn.transaction_type == "credit"
        assert txn.amount == Decimal("5000.00")
        assert txn.status == "reconciled"
        assert txn.sync_source == "manual"

    def test_negative_initial_balance_credit_card(self, service, user):
        account = service.create_manual_account(
            user=user,
            name="New CC",
            account_type="credit_card",
            initial_balance=Decimal("-500.00"),
        )

        account.refresh_from_db()
        assert account.balance == Decimal("-500.00")
        assert account.is_liability is True

        txn = Transaction.objects.get(account=account, description="Opening Balance")
        assert txn.transaction_type == "debit"
        assert txn.amount == Decimal("500.00")

    def test_zero_initial_balance_no_transaction(self, service, user):
        account = service.create_manual_account(
            user=user,
            name="Empty Account",
            account_type="savings",
            initial_balance=Decimal("0"),
        )

        account.refresh_from_db()
        assert account.balance == Decimal("0")
        assert not Transaction.objects.filter(account=account, description="Opening Balance").exists()

    def test_opening_balance_creates_history(self, service, user):
        account = service.create_manual_account(
            user=user,
            name="History Test",
            account_type="checking",
            initial_balance=Decimal("2500.00"),
        )

        history = AccountBalanceHistory.objects.filter(account=account, date=date.today()).first()
        assert history is not None
        assert history.balance == Decimal("2500.00")

    def test_credit_card_sets_is_liability(self, service, user):
        account = service.create_manual_account(
            user=user,
            name="Auto Liability",
            account_type="credit_card",
            initial_balance=Decimal("0"),
        )
        assert account.is_liability is True

    def test_checking_not_liability(self, service, user):
        account = service.create_manual_account(
            user=user,
            name="Checking",
            account_type="checking",
            initial_balance=Decimal("100.00"),
        )
        assert account.is_liability is False
