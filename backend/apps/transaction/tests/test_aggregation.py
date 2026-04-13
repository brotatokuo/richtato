"""Integration tests for income/expense aggregation after manual transactions.

Verifies that the entire chain -- create transaction via TransactionService,
then query aggregations via TransactionService and AssetDashboardRepository --
produces consistent and correct numbers.
"""

from datetime import date
from decimal import Decimal

import pytest

from apps.asset_dashboard.repositories.asset_dashboard_repository import (
    AssetDashboardRepository,
)
from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory
from apps.transaction.services.transaction_service import TransactionService


@pytest.fixture
def user(db):
    return User.objects.create_user(username="aggtest", email="agg@test.com", password="testpass123")


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Checking",
        account_type="checking",
        balance=Decimal("0.00"),
    )


@pytest.fixture
def income_category(user):
    """Income category with a unique slug that won't collide with defaults."""
    return TransactionCategory.objects.create(user=user, name="Test Salary", slug="test-salary-agg", type="income")


@pytest.fixture
def expense_category(user):
    return TransactionCategory.objects.create(
        user=user, name="Test Groceries", slug="test-groceries-agg", type="expense"
    )


@pytest.fixture
def investment_category(user):
    return TransactionCategory.objects.create(user=user, name="Test 401k", slug="test-401k-agg", type="investment")


@pytest.fixture
def transfer_category(user):
    return TransactionCategory.objects.create(
        user=user,
        name="Credit Card Payment",
        slug="credit-card-payment-agg",
        type="transfer",
    )


@pytest.fixture
def tx_service():
    return TransactionService()


@pytest.fixture
def dashboard_repo():
    return AssetDashboardRepository()


# ---------------------------------------------------------------------------
# TransactionService.get_transaction_summary
# ---------------------------------------------------------------------------
class TestTransactionSummary:
    """Tests for TransactionService.get_transaction_summary aggregation."""

    def test_empty_range_returns_zeros(self, tx_service, user):
        result = tx_service.get_transaction_summary(user, date(2025, 1, 1), date(2025, 1, 31))
        assert result["total_income"] == Decimal("0")
        assert result["total_expenses"] == Decimal("0")
        assert result["net"] == Decimal("0")
        assert result["total_transactions"] == 0

    def test_single_income_transaction(self, tx_service, user, account, income_category):
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 15),
            amount=Decimal("3000.00"),
            description="March salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        result = tx_service.get_transaction_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_income"] == Decimal("3000.00")
        assert result["total_expenses"] == Decimal("0")
        assert result["net"] == Decimal("3000.00")
        assert result["total_transactions"] == 1

    def test_single_expense_transaction(self, tx_service, user, account, expense_category):
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 20),
            amount=Decimal("85.50"),
            description="Costco run",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        result = tx_service.get_transaction_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_income"] == Decimal("0")
        assert result["total_expenses"] == Decimal("85.50")
        assert result["net"] == Decimal("-85.50")

    def test_mixed_income_and_expenses(self, tx_service, user, account, income_category, expense_category):
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("5000.00"),
            description="Salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 5),
            amount=Decimal("1200.00"),
            description="Rent",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 10),
            amount=Decimal("200.00"),
            description="Meal prep",
            transaction_type="debit",
            category_id=expense_category.id,
        )

        result = tx_service.get_transaction_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_income"] == Decimal("5000.00")
        assert result["total_expenses"] == Decimal("1400.00")
        assert result["net"] == Decimal("3600.00")
        assert result["total_transactions"] == 3

    def test_date_range_filters_correctly(self, tx_service, user, account, expense_category):
        """Transactions outside the range should not be counted."""
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 2, 28),
            amount=Decimal("100.00"),
            description="Feb expense",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 15),
            amount=Decimal("200.00"),
            description="March expense",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 4, 1),
            amount=Decimal("300.00"),
            description="April expense",
            transaction_type="debit",
            category_id=expense_category.id,
        )

        result = tx_service.get_transaction_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_expenses"] == Decimal("200.00")
        assert result["total_transactions"] == 1

    def test_by_category_grouping(self, tx_service, user, account, income_category, expense_category):
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("5000.00"),
            description="Salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 10),
            amount=Decimal("50.00"),
            description="Weekly shop",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 12),
            amount=Decimal("80.00"),
            description="More food",
            transaction_type="debit",
            category_id=expense_category.id,
        )

        result = tx_service.get_transaction_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert "Test Salary" in result["by_category"]
        assert result["by_category"]["Test Salary"]["count"] == 1
        assert result["by_category"]["Test Salary"]["total"] == Decimal("5000.00")
        assert "Test Groceries" in result["by_category"]
        assert result["by_category"]["Test Groceries"]["count"] == 2
        assert result["by_category"]["Test Groceries"]["total"] == Decimal("130.00")


# ---------------------------------------------------------------------------
# TransactionService.get_cashflow_summary
# ---------------------------------------------------------------------------
class TestCashflowSummary:
    """Tests for TransactionService.get_cashflow_summary (DB-level aggregation)."""

    def test_empty_range_returns_zeros(self, tx_service, user):
        result = tx_service.get_cashflow_summary(user, date(2025, 1, 1), date(2025, 1, 31))
        assert result["total_income"] == 0.0
        assert result["total_expenses"] == 0.0
        assert result["total_investments"] == 0.0
        assert result["net_savings"] == 0.0

    def test_income_and_expense_totals(self, tx_service, user, account, income_category, expense_category):
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("4000.00"),
            description="Salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 10),
            amount=Decimal("150.00"),
            description="Weekly shop",
            transaction_type="debit",
            category_id=expense_category.id,
        )

        result = tx_service.get_cashflow_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_income"] == 4000.0
        assert result["total_expenses"] == 150.0
        assert result["net_savings"] == 3850.0

    def test_investment_separated_from_expenses(self, tx_service, user, account, expense_category, investment_category):
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 5),
            amount=Decimal("500.00"),
            description="401k contribution",
            transaction_type="debit",
            category_id=investment_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 10),
            amount=Decimal("200.00"),
            description="Weekly shop",
            transaction_type="debit",
            category_id=expense_category.id,
        )

        result = tx_service.get_cashflow_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_investments"] == 500.0
        assert result["total_expenses"] == 200.0
        assert result["investments_by_category"]["Test 401k"] == 500.0
        assert result["expenses_by_category"]["Test Groceries"] == 200.0

    def test_net_savings_formula(
        self,
        tx_service,
        user,
        account,
        income_category,
        expense_category,
        investment_category,
    ):
        """net_savings = income - expenses - investments."""
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("6000.00"),
            description="Salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 5),
            amount=Decimal("2000.00"),
            description="Rent",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 10),
            amount=Decimal("1000.00"),
            description="Invest",
            transaction_type="debit",
            category_id=investment_category.id,
        )

        result = tx_service.get_cashflow_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_income"] == 6000.0
        assert result["total_expenses"] == 2000.0
        assert result["total_investments"] == 1000.0
        assert result["net_savings"] == 3000.0

    def test_uncategorized_credit_excluded_from_income(self, user, account):
        """Auto-uncategorized credits (type='other') are not counted as income.

        Transaction.save() auto-assigns the 'Uncategorized' category with
        type='other'. Since cashflow_summary now uses the canonical category-type
        filter (category__type='income'), these are excluded — consistent with
        AssetDashboardRepository.
        """
        Transaction.objects.create(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("250.00"),
            description="xyzunknown123",
            transaction_type="credit",
            category=None,
        )
        tx_service = TransactionService()
        result = tx_service.get_cashflow_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_income"] == 0.0

    def test_uncategorized_debit_excluded_from_expenses(self, user, account):
        """Auto-uncategorized debits (type='other') are not counted as expenses.

        Same rationale as above: canonical filters require an explicit category
        type to classify transactions.
        """
        Transaction.objects.create(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("75.00"),
            description="xyzunknown456",
            transaction_type="debit",
            category=None,
        )
        tx_service = TransactionService()
        result = tx_service.get_cashflow_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        assert result["total_expenses"] == 0.0


# ---------------------------------------------------------------------------
# AssetDashboardRepository aggregation (income/expense sums)
# ---------------------------------------------------------------------------
class TestDashboardRepoAggregation:
    """Tests for AssetDashboardRepository income/expense sums with real transactions."""

    def test_income_sum_with_categorized_credits(self, dashboard_repo, user, account, income_category, tx_service):
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("3000.00"),
            description="Salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 15),
            amount=Decimal("500.00"),
            description="Freelance gig",
            transaction_type="credit",
            category_id=income_category.id,
        )

        total = dashboard_repo.get_income_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31))
        assert total == Decimal("3500.00")

    def test_expense_sum_with_categorized_debits(self, dashboard_repo, user, account, expense_category, tx_service):
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 5),
            amount=Decimal("1200.00"),
            description="Rent",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 10),
            amount=Decimal("60.00"),
            description="Gas fill",
            transaction_type="debit",
            category_id=expense_category.id,
        )

        total = dashboard_repo.get_expense_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31))
        assert total == Decimal("1260.00")

    def test_auto_uncategorized_credit_excluded_from_income(self, dashboard_repo, user, account):
        """Transaction.save() auto-assigns the 'Uncategorized' category (type='other').

        Since all surfaces now use the canonical category-type filters,
        auto-uncategorized credits are consistently excluded from income sums.
        """
        Transaction.objects.create(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("100.00"),
            description="xyzunknown789",
            transaction_type="credit",
            category=None,
        )
        total = dashboard_repo.get_income_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31))
        assert total == Decimal("0")

    def test_auto_uncategorized_debit_excluded_from_expenses(self, dashboard_repo, user, account):
        """Same as above — auto-uncategorized debits (type='other') are excluded from expenses."""
        Transaction.objects.create(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("50.00"),
            description="xyzunknown000",
            transaction_type="debit",
            category=None,
        )
        total = dashboard_repo.get_expense_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31))
        assert total == Decimal("0")

    def test_credit_card_payment_excluded_from_expenses(
        self, dashboard_repo, user, account, transfer_category, tx_service
    ):
        """Transactions categorized as 'credit-card-payment' should not appear in expenses."""
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("500.00"),
            description="CC payment",
            transaction_type="debit",
            category_id=transfer_category.id,
        )
        total = dashboard_repo.get_expense_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31))
        assert total == Decimal("0")

    def test_investment_not_double_counted_in_expenses(
        self, dashboard_repo, user, account, investment_category, tx_service
    ):
        """Investment-type debits should NOT appear in expense sums."""
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("1000.00"),
            description="401k contribution",
            transaction_type="debit",
            category_id=investment_category.id,
        )
        total = dashboard_repo.get_expense_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31))
        assert total == Decimal("0")

    def test_deleted_transactions_not_counted(self, dashboard_repo, user, account, income_category, tx_service):
        """After deleting a transaction, sums should reflect the removal."""
        tx = tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("2000.00"),
            description="Salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        assert dashboard_repo.get_income_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31)) == Decimal(
            "2000.00"
        )

        tx_service.delete_transaction(tx)
        assert dashboard_repo.get_income_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31)) == Decimal("0")

    def test_updated_amount_reflected_in_sums(self, dashboard_repo, user, account, expense_category, tx_service):
        """After updating a transaction's amount, sums should reflect the new value."""
        tx = tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("100.00"),
            description="Weekly shop",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        assert dashboard_repo.get_expense_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31)) == Decimal(
            "100.00"
        )

        tx_service.update_transaction(tx, amount=Decimal("250.00"))
        assert dashboard_repo.get_expense_sum_by_date_range(user, date(2025, 3, 1), date(2025, 3, 31)) == Decimal(
            "250.00"
        )


# ---------------------------------------------------------------------------
# Balance consistency after manual transactions
# ---------------------------------------------------------------------------
class TestBalanceConsistencyAfterAggregation:
    """Verify that account.balance and aggregation totals are consistent."""

    def test_balance_equals_initial_plus_net_transactions(
        self,
        tx_service,
        user,
        account,
        income_category,
        expense_category,
    ):
        """account.balance should equal initial_balance + sum(credits) - sum(debits)."""
        initial = account.balance  # 0.00

        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("5000.00"),
            description="Salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 5),
            amount=Decimal("1200.00"),
            description="Rent",
            transaction_type="debit",
            category_id=expense_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 10),
            amount=Decimal("80.00"),
            description="Weekly shop",
            transaction_type="debit",
            category_id=expense_category.id,
        )

        account.refresh_from_db()
        expected = initial + Decimal("5000.00") - Decimal("1200.00") - Decimal("80.00")
        assert account.balance == expected

    def test_balance_and_summary_net_agree(
        self,
        tx_service,
        user,
        account,
        income_category,
        expense_category,
    ):
        """The net from get_transaction_summary should equal the balance change."""
        initial = account.balance

        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 1),
            amount=Decimal("3000.00"),
            description="Salary",
            transaction_type="credit",
            category_id=income_category.id,
        )
        tx_service.create_manual_transaction(
            user=user,
            account=account,
            date=date(2025, 3, 15),
            amount=Decimal("700.00"),
            description="Bills",
            transaction_type="debit",
            category_id=expense_category.id,
        )

        summary = tx_service.get_transaction_summary(user, date(2025, 3, 1), date(2025, 3, 31))
        account.refresh_from_db()
        balance_change = account.balance - initial

        assert balance_change == summary["net"]
