"""Tests for TransactionService with balance impact."""

from datetime import date
from decimal import Decimal

import pytest

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import TransactionCategory
from apps.transaction.services.transaction_service import TransactionService


@pytest.fixture
def user(db):
    return User.objects.create_user(username="svctest", email="svc@test.com", password="testpass123")


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Service Test Account",
        account_type="checking",
        balance=Decimal("10000.00"),
    )


@pytest.fixture
def category(user):
    return TransactionCategory.objects.create(
        user=user, name="Test Groceries", slug="test-groceries-svc", type="expense"
    )


@pytest.fixture
def service():
    return TransactionService()


class TestCreateManualTransaction:
    def test_creates_transaction_and_updates_balance(self, service, user, account):
        tx = service.create_manual_transaction(
            user=user,
            account=account,
            date=date.today(),
            amount=Decimal("75.50"),
            description="Test purchase",
            transaction_type="debit",
        )
        assert tx.id is not None
        assert tx.amount == Decimal("75.50")
        assert tx.sync_source == "manual"

        account.refresh_from_db()
        assert account.balance == Decimal("9924.50")

    def test_creates_credit_transaction(self, service, user, account):
        tx = service.create_manual_transaction(
            user=user,
            account=account,
            date=date.today(),
            amount=Decimal("500.00"),
            description="Refund",
            transaction_type="credit",
        )
        assert tx.transaction_type == "credit"

        account.refresh_from_db()
        assert account.balance == Decimal("10500.00")

    def test_creates_with_category(self, service, user, account, category):
        tx = service.create_manual_transaction(
            user=user,
            account=account,
            date=date.today(),
            amount=Decimal("42.00"),
            description="Costco run",
            transaction_type="debit",
            category_id=category.id,
        )
        assert tx.category == category

    def test_creates_balance_history(self, service, user, account):
        today = date.today()
        service.create_manual_transaction(
            user=user,
            account=account,
            date=today,
            amount=Decimal("100.00"),
            description="Test",
            transaction_type="debit",
        )
        assert AccountBalanceHistory.objects.filter(account=account, date=today).exists()


class TestUpdateTransaction:
    def test_update_amount_adjusts_balance(self, service, user, account):
        tx = service.create_manual_transaction(
            user=user,
            account=account,
            date=date.today(),
            amount=Decimal("100.00"),
            description="Original",
            transaction_type="debit",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("9900.00")

        service.update_transaction(tx, amount=Decimal("300.00"))
        account.refresh_from_db()
        assert account.balance == Decimal("9700.00")

    def test_update_description_no_balance_change(self, service, user, account):
        tx = service.create_manual_transaction(
            user=user,
            account=account,
            date=date.today(),
            amount=Decimal("50.00"),
            description="Old desc",
            transaction_type="debit",
        )
        account.refresh_from_db()
        original_balance = account.balance

        service.update_transaction(tx, description="New desc")
        account.refresh_from_db()
        assert account.balance == original_balance


class TestDeleteTransaction:
    def test_delete_reverses_balance(self, service, user, account):
        tx = service.create_manual_transaction(
            user=user,
            account=account,
            date=date.today(),
            amount=Decimal("250.00"),
            description="Will delete",
            transaction_type="debit",
        )
        account.refresh_from_db()
        assert account.balance == Decimal("9750.00")

        service.delete_transaction(tx)
        account.refresh_from_db()
        assert account.balance == Decimal("10000.00")

    def test_delete_removes_orphaned_history(self, service, user, account):
        today = date.today()
        tx = service.create_manual_transaction(
            user=user,
            account=account,
            date=today,
            amount=Decimal("50.00"),
            description="Solo tx",
            transaction_type="debit",
        )
        assert AccountBalanceHistory.objects.filter(account=account, date=today).exists()

        service.delete_transaction(tx)
        assert not AccountBalanceHistory.objects.filter(account=account, date=today).exists()
