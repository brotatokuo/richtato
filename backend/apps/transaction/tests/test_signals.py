"""Tests for transaction signals that maintain account balance and history."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="signaltest", email="signal@test.com", password="testpass123"
    )


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Test Checking",
        account_type="checking",
        balance=Decimal("5000.00"),
    )


class TestBalanceUpdateOnCreate:
    """Creating a transaction should adjust account.balance."""

    def test_credit_increases_balance(self, account):
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=date.today(),
            amount=Decimal("200.00"),
            transaction_type="credit",
            description="Deposit",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("5200.00")

    def test_debit_decreases_balance(self, account):
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=date.today(),
            amount=Decimal("150.00"),
            transaction_type="debit",
            description="Purchase",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("4850.00")

    def test_multiple_transactions_accumulate(self, account):
        today = date.today()
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("1000.00"),
            transaction_type="credit",
            description="Salary",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("300.00"),
            transaction_type="debit",
            description="Rent",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("5700.00")


class TestBalanceUpdateOnDelete:
    """Deleting a transaction should reverse its effect on account.balance."""

    def test_delete_credit_decreases_balance(self, account):
        tx = Transaction.objects.create(
            user=account.user,
            account=account,
            date=date.today(),
            amount=Decimal("500.00"),
            transaction_type="credit",
            description="Deposit",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("5500.00")

        tx.delete()
        account.refresh_from_db()
        assert account.balance == Decimal("5000.00")

    def test_delete_debit_increases_balance(self, account):
        tx = Transaction.objects.create(
            user=account.user,
            account=account,
            date=date.today(),
            amount=Decimal("200.00"),
            transaction_type="debit",
            description="Coffee",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("4800.00")

        tx.delete()
        account.refresh_from_db()
        assert account.balance == Decimal("5000.00")


class TestBalanceUpdateOnUpdate:
    """Updating a transaction should adjust the balance delta correctly."""

    def test_increase_amount(self, account):
        tx = Transaction.objects.create(
            user=account.user,
            account=account,
            date=date.today(),
            amount=Decimal("100.00"),
            transaction_type="debit",
            description="Groceries",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("4900.00")

        tx.amount = Decimal("250.00")
        tx.save()
        account.refresh_from_db()
        assert account.balance == Decimal("4750.00")

    def test_change_type_credit_to_debit(self, account):
        tx = Transaction.objects.create(
            user=account.user,
            account=account,
            date=date.today(),
            amount=Decimal("100.00"),
            transaction_type="credit",
            description="Refund",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("5100.00")

        tx.transaction_type = "debit"
        tx.save()
        account.refresh_from_db()
        # Was +100, now -100 → delta of -200
        assert account.balance == Decimal("4900.00")


class TestBalanceHistoryOnCreate:
    """AccountBalanceHistory should be correctly derived after transaction creation."""

    def test_single_transaction_today(self, account):
        today = date.today()
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("200.00"),
            transaction_type="credit",
            description="Deposit",
        )
        history = AccountBalanceHistory.objects.get(account=account, date=today)
        # Balance is 5200, no transactions after today → history = 5200
        assert history.balance == Decimal("5200.00")

    def test_transaction_in_past(self, account):
        today = date.today()
        yesterday = today - timedelta(days=1)

        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("100.00"),
            transaction_type="debit",
            description="Today expense",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=yesterday,
            amount=Decimal("300.00"),
            transaction_type="credit",
            description="Yesterday deposit",
        )

        account.refresh_from_db()
        # balance = 5000 + (-100) + 300 = 5200
        assert account.balance == Decimal("5200.00")

        today_hist = AccountBalanceHistory.objects.get(account=account, date=today)
        yesterday_hist = AccountBalanceHistory.objects.get(
            account=account, date=yesterday
        )

        # Today: anchor 5200 - 0 transactions after today = 5200
        assert today_hist.balance == Decimal("5200.00")
        # Yesterday: anchor 5200 - (today's net: -100 debit) = 5200 - (-100) = 5300
        assert yesterday_hist.balance == Decimal("5300.00")

    def test_multiple_transactions_same_date(self, account):
        today = date.today()
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("500.00"),
            transaction_type="credit",
            description="Salary",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("100.00"),
            transaction_type="debit",
            description="Lunch",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("5400.00")

        history = AccountBalanceHistory.objects.get(account=account, date=today)
        assert history.balance == Decimal("5400.00")

    def test_transactions_across_multiple_dates(self, account):
        d1 = date(2025, 1, 10)
        d2 = date(2025, 1, 15)
        d3 = date(2025, 1, 20)

        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d1,
            amount=Decimal("1000.00"),
            transaction_type="credit",
            description="Day 1",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d2,
            amount=Decimal("200.00"),
            transaction_type="debit",
            description="Day 2",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d3,
            amount=Decimal("300.00"),
            transaction_type="debit",
            description="Day 3",
        )

        account.refresh_from_db()
        # 5000 + 1000 - 200 - 300 = 5500
        assert account.balance == Decimal("5500.00")

        h1 = AccountBalanceHistory.objects.get(account=account, date=d1)
        h2 = AccountBalanceHistory.objects.get(account=account, date=d2)
        h3 = AccountBalanceHistory.objects.get(account=account, date=d3)

        # d3 (latest): anchor 5500 - 0 after = 5500
        assert h3.balance == Decimal("5500.00")
        # d2: anchor 5500 - (-300 debit after d2) = 5500 - (-300) = 5800
        assert h2.balance == Decimal("5800.00")
        # d1: anchor 5500 - (-200 -300 debits + 0 credits after d1) = 5500 - (-500) = 6000
        assert h1.balance == Decimal("6000.00")


class TestBalanceHistoryOnDelete:
    """Deleting a transaction should update history and clean up orphaned entries."""

    def test_delete_only_transaction_removes_history(self, account):
        today = date.today()
        tx = Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("100.00"),
            transaction_type="debit",
            description="Only tx",
        )
        assert AccountBalanceHistory.objects.filter(
            account=account, date=today
        ).exists()

        tx.delete()
        assert not AccountBalanceHistory.objects.filter(
            account=account, date=today
        ).exists()

    def test_delete_one_of_two_same_date_keeps_history(self, account):
        today = date.today()
        tx1 = Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("100.00"),
            transaction_type="credit",
            description="First",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("50.00"),
            transaction_type="debit",
            description="Second",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("5050.00")

        tx1.delete()
        account.refresh_from_db()
        assert account.balance == Decimal("4950.00")

        history = AccountBalanceHistory.objects.get(account=account, date=today)
        assert history.balance == Decimal("4950.00")


class TestDateChangeRecalculation:
    """Moving a transaction to a different date should recalculate both dates."""

    def test_move_transaction_to_later_date(self, account):
        d1 = date(2025, 3, 1)
        d2 = date(2025, 3, 10)

        tx = Transaction.objects.create(
            user=account.user,
            account=account,
            date=d1,
            amount=Decimal("500.00"),
            transaction_type="credit",
            description="Moveable",
        )
        assert AccountBalanceHistory.objects.filter(
            account=account, date=d1
        ).exists()

        tx.date = d2
        tx.save()

        # Old date should be cleaned up (no transactions left on d1)
        assert not AccountBalanceHistory.objects.filter(
            account=account, date=d1
        ).exists()
        # New date should have the history entry
        history = AccountBalanceHistory.objects.get(account=account, date=d2)
        assert history.balance == Decimal("5500.00")
