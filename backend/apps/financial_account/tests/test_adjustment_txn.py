"""Tests for manual balance adjustment via AccountBalanceService."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.financial_account.services.account_balance_service import (
    AccountBalanceService,
)
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


@pytest.fixture
def user(db):
    return User.objects.create_user(username="adjtest", email="adj@test.com", password="testpass123")


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Adjustment Test",
        account_type="checking",
        balance=Decimal("5000.00"),
    )


@pytest.fixture
def service():
    return AccountBalanceService()


class TestManualBalanceAdjustment:
    """Setting an absolute balance should create an adjustment transaction."""

    def test_set_higher_balance_creates_credit(self, service, account):
        result = service.update_balance(account, Decimal("6000.00"))

        assert result.account.balance == Decimal("6000.00")
        assert result.computed_balance == Decimal("5000.00")
        assert result.adjustment == Decimal("1000.00")

        adj = Transaction.objects.filter(account=account, description="Balance Adjustment").first()
        assert adj is not None
        assert adj.transaction_type == "credit"
        assert adj.amount == Decimal("1000.00")
        assert adj.status == "reconciled"
        assert result.adjustment_transaction == adj

    def test_set_lower_balance_creates_debit(self, service, account):
        result = service.update_balance(account, Decimal("3000.00"))

        assert result.account.balance == Decimal("3000.00")

        adj = Transaction.objects.filter(account=account, description="Balance Adjustment").first()
        assert adj is not None
        assert adj.transaction_type == "debit"
        assert adj.amount == Decimal("2000.00")

    def test_set_same_balance_no_transaction(self, service, account):
        result = service.update_balance(account, Decimal("5000.00"))

        assert result.account.balance == Decimal("5000.00")
        assert result.adjustment == Decimal("0")
        assert result.adjustment_transaction is None
        assert not Transaction.objects.filter(account=account, description="Balance Adjustment").exists()

    def test_set_balance_on_past_date(self, service, account):
        yesterday = date.today() - timedelta(days=1)
        result = service.update_balance(account, Decimal("4000.00"), balance_date=yesterday)

        assert result.account.balance == Decimal("4000.00")
        adj = Transaction.objects.get(account=account, description="Balance Adjustment")
        assert adj.date == yesterday

    def test_past_date_with_later_transactions(self, service, account, user):
        """Past-date reconciliation adjusts anchor by delta from computed balance, not raw anchor."""
        yesterday = date.today() - timedelta(days=1)
        Transaction.objects.create(
            user=user,
            account=account,
            date=date.today(),
            amount=Decimal("1000.00"),
            transaction_type="credit",
            description="Deposit",
            sync_source="manual",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("6000.00")

        result = service.update_balance(account, Decimal("4500.00"), balance_date=yesterday)

        assert result.computed_balance == Decimal("5000.00")
        assert result.adjustment == Decimal("-500.00")
        assert result.account.balance == Decimal("5500.00")

        adj = Transaction.objects.get(account=account, description="Balance Adjustment")
        assert adj.date == yesterday
        assert adj.transaction_type == "debit"
        assert adj.amount == Decimal("500.00")

    def test_adjustment_creates_history_entry(self, service, account):
        today = date.today()
        service.update_balance(account, Decimal("7500.00"), balance_date=today)

        history = AccountBalanceHistory.objects.filter(account=account, date=today).first()
        assert history is not None
        assert history.balance == Decimal("7500.00")

    def test_set_negative_balance(self, service, account):
        result = service.update_balance(account, Decimal("-500.00"))
        assert result.account.balance == Decimal("-500.00")

        adj = Transaction.objects.get(account=account, description="Balance Adjustment")
        assert adj.transaction_type == "debit"
        assert adj.amount == Decimal("5500.00")

    def test_multiple_adjustments_accumulate(self, service, account):
        service.update_balance(account, Decimal("6000.00"))
        service.update_balance(account, Decimal("4000.00"))

        account.refresh_from_db()
        assert account.balance == Decimal("4000.00")

        adjustments = Transaction.objects.filter(account=account, description="Balance Adjustment")
        assert adjustments.count() == 2
