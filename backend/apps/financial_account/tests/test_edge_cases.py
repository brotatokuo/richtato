"""Edge case tests for balance tracking."""

from datetime import date
from decimal import Decimal

import pytest
from apps.asset_dashboard.repositories.asset_dashboard_repository import (
    AssetDashboardRepository,
)
from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="edgetest", email="edge@test.com", password="testpass123"
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
        name="Edge Case Account",
        account_type="checking",
        balance=Decimal("1000.00"),
    )


@pytest.fixture
def repo():
    return AssetDashboardRepository()


class TestZeroBalanceAccount:
    """Accounts with zero balance should behave correctly."""

    def test_zero_balance_in_networth(self, repo, user):
        FinancialAccount.objects.create(
            user=user,
            name="Zero Balance",
            account_type="checking",
            balance=Decimal("0"),
        )
        nw = repo.get_networth(user)
        assert nw == Decimal("0")

    def test_debit_below_zero(self, account):
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=date.today(),
            amount=Decimal("2000.00"),
            transaction_type="debit",
            description="Overdraft",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("-1000.00")


class TestInactiveAccountExclusion:
    """Inactive accounts should be excluded from net worth."""

    def test_deactivated_account_excluded(self, repo, user, account):
        nw_before = repo.get_networth(user)
        assert nw_before == Decimal("1000.00")

        account.is_active = False
        account.save()

        nw_after = repo.get_networth(user)
        assert nw_after == Decimal("0")

    def test_deactivated_account_excluded_from_liabilities(self, repo, user):
        cc = FinancialAccount.objects.create(
            user=user,
            name="Inactive CC",
            account_type="credit_card",
            balance=Decimal("-500.00"),
            is_liability=True,
            is_active=False,
        )
        liabilities = repo.get_total_liabilities(user)
        assert liabilities == Decimal("0")


class TestVeryLargeBalance:
    """Max digits=15 should handle large values."""

    def test_large_balance_account(self, repo, user):
        FinancialAccount.objects.create(
            user=user,
            name="Big Balance",
            account_type="savings",
            balance=Decimal("9999999999.99"),
        )
        nw = repo.get_networth(user)
        assert nw == Decimal("9999999999.99")

    def test_large_transaction(self, account):
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=date.today(),
            amount=Decimal("9999999999.99"),
            transaction_type="credit",
            description="Large deposit",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("10000000999.99")


class TestCascadingDeletes:
    """Deleting an account should cascade to history."""

    def test_hard_delete_cascades_history(self, user):
        acct = FinancialAccount.objects.create(
            user=user,
            name="Cascade Test",
            account_type="checking",
            balance=Decimal("500.00"),
        )
        AccountBalanceHistory.objects.create(
            account=acct, date=date.today(), balance=Decimal("500.00")
        )
        assert AccountBalanceHistory.objects.filter(account=acct).count() == 1

        acct_id = acct.id
        acct.delete()

        assert not AccountBalanceHistory.objects.filter(account_id=acct_id).exists()

    def test_hard_delete_cascades_transactions(self, user):
        acct = FinancialAccount.objects.create(
            user=user,
            name="Cascade Txn Test",
            account_type="checking",
            balance=Decimal("0"),
        )
        Transaction.objects.create(
            user=user,
            account=acct,
            date=date.today(),
            amount=Decimal("100.00"),
            transaction_type="debit",
            description="Will cascade",
        )

        acct_id = acct.id
        acct.delete()
        assert not Transaction.objects.filter(account_id=acct_id).exists()


class TestDateBoundaries:
    """Transactions at date boundaries should be handled correctly."""

    def test_year_end_transaction(self, account):
        d1 = date(2025, 12, 31)
        d2 = date(2026, 1, 1)

        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d1,
            amount=Decimal("100.00"),
            transaction_type="debit",
            description="NYE expense",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d2,
            amount=Decimal("200.00"),
            transaction_type="credit",
            description="New Year deposit",
        )

        account.refresh_from_db()
        assert account.balance == Decimal("1100.00")

        h1 = AccountBalanceHistory.objects.get(account=account, date=d1)
        h2 = AccountBalanceHistory.objects.get(account=account, date=d2)

        assert h2.balance == Decimal("1100.00")
        # h1: 1100 - 200 (credit after d1) = 900
        assert h1.balance == Decimal("900.00")

    def test_same_date_credit_and_debit(self, account):
        today = date.today()
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("500.00"),
            transaction_type="credit",
            description="Income",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("500.00"),
            transaction_type="debit",
            description="Expense",
        )

        account.refresh_from_db()
        assert account.balance == Decimal("1000.00")

        history = AccountBalanceHistory.objects.get(account=account, date=today)
        assert history.balance == Decimal("1000.00")


class TestCreditCardSignConvention:
    """Credit card balances should be stored as negative."""

    def test_cc_debit_makes_more_negative(self, user):
        cc = FinancialAccount.objects.create(
            user=user,
            name="Test CC",
            account_type="credit_card",
            balance=Decimal("-500.00"),
            is_liability=True,
        )
        Transaction.objects.create(
            user=user,
            account=cc,
            date=date.today(),
            amount=Decimal("200.00"),
            transaction_type="debit",
            description="Purchase",
        )
        cc.refresh_from_db()
        assert cc.balance == Decimal("-700.00")

    def test_cc_credit_makes_less_negative(self, user):
        cc = FinancialAccount.objects.create(
            user=user,
            name="Test CC",
            account_type="credit_card",
            balance=Decimal("-500.00"),
            is_liability=True,
        )
        Transaction.objects.create(
            user=user,
            account=cc,
            date=date.today(),
            amount=Decimal("200.00"),
            transaction_type="credit",
            description="Payment",
        )
        cc.refresh_from_db()
        assert cc.balance == Decimal("-300.00")

    def test_cc_networth_contribution(self, repo, user):
        FinancialAccount.objects.create(
            user=user,
            name="Checking",
            account_type="checking",
            balance=Decimal("10000.00"),
        )
        FinancialAccount.objects.create(
            user=user,
            name="CC",
            account_type="credit_card",
            balance=Decimal("-3000.00"),
            is_liability=True,
        )
        nw = repo.get_networth(user)
        assert nw == Decimal("7000.00")
