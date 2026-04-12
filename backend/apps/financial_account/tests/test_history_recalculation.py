"""Tests for balance history recalculation from anchor."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


@pytest.fixture
def user(db):
    return User.objects.create_user(username="histtest", email="hist@test.com", password="testpass123")


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="History Test",
        account_type="checking",
        balance=Decimal("10000.00"),
    )


class TestHistoryBackfill:
    """30 days of transactions should produce correct daily history."""

    def test_many_days_of_transactions(self, account):
        base = date(2025, 6, 1)
        for i in range(30):
            Transaction.objects.create(
                user=account.user,
                account=account,
                date=base + timedelta(days=i),
                amount=Decimal("100.00"),
                transaction_type="debit",
                description=f"Day {i + 1}",
            )

        account.refresh_from_db()
        # 10000 - 30*100 = 7000
        assert account.balance == Decimal("7000.00")

        history_count = AccountBalanceHistory.objects.filter(account=account).count()
        assert history_count == 30

        last_day = AccountBalanceHistory.objects.get(account=account, date=base + timedelta(days=29))
        assert last_day.balance == Decimal("7000.00")

        first_day = AccountBalanceHistory.objects.get(account=account, date=base)
        # day 1: anchor 7000 - net_after_day1 = 7000 - (-2900) = 9900
        assert first_day.balance == Decimal("9900.00")


class TestEditOldTransaction:
    """Editing an old transaction should cascade recalculation."""

    def test_edit_amount_recalculates_subsequent_dates(self, account):
        d1 = date(2025, 6, 1)
        d2 = date(2025, 6, 5)
        d3 = date(2025, 6, 10)

        tx1 = Transaction.objects.create(
            user=account.user,
            account=account,
            date=d1,
            amount=Decimal("500.00"),
            transaction_type="debit",
            description="First",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d2,
            amount=Decimal("200.00"),
            transaction_type="debit",
            description="Second",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d3,
            amount=Decimal("300.00"),
            transaction_type="debit",
            description="Third",
        )

        account.refresh_from_db()
        assert account.balance == Decimal("9000.00")

        # Edit first transaction: 500 → 800
        tx1.amount = Decimal("800.00")
        tx1.save()

        account.refresh_from_db()
        assert account.balance == Decimal("8700.00")

        h1 = AccountBalanceHistory.objects.get(account=account, date=d1)
        h2 = AccountBalanceHistory.objects.get(account=account, date=d2)
        h3 = AccountBalanceHistory.objects.get(account=account, date=d3)

        assert h3.balance == Decimal("8700.00")
        assert h2.balance == Decimal("9000.00")
        assert h1.balance == Decimal("9200.00")


class TestDeleteMiddleTransaction:
    """Deleting a transaction in the middle should recalculate."""

    def test_delete_middle_recalculates_all(self, account):
        d1 = date(2025, 6, 1)
        d2 = date(2025, 6, 5)
        d3 = date(2025, 6, 10)

        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d1,
            amount=Decimal("100.00"),
            transaction_type="debit",
            description="First",
        )
        tx2 = Transaction.objects.create(
            user=account.user,
            account=account,
            date=d2,
            amount=Decimal("500.00"),
            transaction_type="debit",
            description="Middle",
        )
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=d3,
            amount=Decimal("200.00"),
            transaction_type="debit",
            description="Last",
        )

        account.refresh_from_db()
        assert account.balance == Decimal("9200.00")

        tx2.delete()
        account.refresh_from_db()
        assert account.balance == Decimal("9700.00")

        # d2 should be removed (no more transactions on that date)
        assert not AccountBalanceHistory.objects.filter(account=account, date=d2).exists()

        h1 = AccountBalanceHistory.objects.get(account=account, date=d1)
        h3 = AccountBalanceHistory.objects.get(account=account, date=d3)

        assert h3.balance == Decimal("9700.00")
        assert h1.balance == Decimal("9900.00")


class TestHistorySourceTracking:
    """Balance history entries from transactions should have source='transaction'."""

    def test_signal_created_history_has_transaction_source(self, account):
        today = date.today()
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=today,
            amount=Decimal("100.00"),
            transaction_type="debit",
            description="Source test",
        )
        history = AccountBalanceHistory.objects.get(account=account, date=today)
        assert history.source == "transaction"
