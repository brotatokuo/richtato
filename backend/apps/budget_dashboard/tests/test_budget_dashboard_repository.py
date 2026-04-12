"""Integration tests for BudgetDashboardRepository."""

from datetime import date
from decimal import Decimal

import pytest
from apps.budget.models import Budget, BudgetCategory
from apps.budget_dashboard.repositories.budget_dashboard_repository import (
    BudgetDashboardRepository,
)
from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="repotest", email="repo@test.com", password="testpass123"
    )


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user, name="Repo Checking", account_type="checking",
        balance=Decimal("10000.00"),
    )


@pytest.fixture
def expense_cat(user):
    return TransactionCategory.objects.create(
        user=user, name="Repo Food", slug="repo-food-dash", type="expense",
    )


@pytest.fixture
def expense_cat_2(user):
    return TransactionCategory.objects.create(
        user=user, name="Repo Clothing", slug="repo-clothing-dash", type="expense",
    )


@pytest.fixture
def income_cat(user):
    return TransactionCategory.objects.create(
        user=user, name="Repo Salary", slug="repo-salary-dash", type="income",
    )


@pytest.fixture
def cc_payment_cat(user):
    """Get the auto-seeded credit-card-payment category (created by user signal)."""
    return TransactionCategory.objects.get(user=user, slug="credit-card-payment")


@pytest.fixture
def repo():
    return BudgetDashboardRepository()


def _txn(user, account, category, amount, txn_date, transaction_type="debit"):
    return Transaction.objects.create(
        user=user, account=account, category=category, amount=amount,
        date=txn_date, description=f"Test {amount}",
        transaction_type=transaction_type, sync_source="manual",
    )


class TestGetExpenseSumByDateRange:
    def test_sums_expense_type_transactions(self, repo, user, account, expense_cat):
        _txn(user, account, expense_cat, Decimal("100.00"), date(2024, 1, 10))
        _txn(user, account, expense_cat, Decimal("50.00"), date(2024, 1, 20))

        result = repo.get_expense_sum_by_date_range(user, date(2024, 1, 1), date(2024, 1, 31))
        assert result == Decimal("150.00")

    def test_includes_uncategorized_debits(self, repo, user, account):
        """Transaction.save() auto-assigns Uncategorized category, which has type='other'.
        The expense filter includes category=None debits, but since save() prevents null
        categories, this path is hit only for legacy data. We test with the uncategorized
        category (type='other') which is NOT matched by _get_expense_filter."""
        uncat = TransactionCategory.get_uncategorized_for_user(user)
        _txn(user, account, uncat, Decimal("75.00"), date(2024, 1, 15))

        result = repo.get_expense_sum_by_date_range(user, date(2024, 1, 1), date(2024, 1, 31))
        # Uncategorized type='other' doesn't match expense filter unless category is actually None
        assert result == Decimal("0")

    def test_excludes_credit_card_payment(self, repo, user, account, cc_payment_cat):
        _txn(user, account, cc_payment_cat, Decimal("500.00"), date(2024, 1, 10))

        result = repo.get_expense_sum_by_date_range(user, date(2024, 1, 1), date(2024, 1, 31))
        assert result == Decimal("0")

    def test_excludes_out_of_range(self, repo, user, account, expense_cat):
        _txn(user, account, expense_cat, Decimal("100.00"), date(2024, 1, 15))
        _txn(user, account, expense_cat, Decimal("50.00"), date(2023, 12, 31))

        result = repo.get_expense_sum_by_date_range(user, date(2024, 1, 1), date(2024, 1, 31))
        assert result == Decimal("100.00")

    def test_returns_zero_when_no_transactions(self, repo, user):
        result = repo.get_expense_sum_by_date_range(user, date(2024, 1, 1), date(2024, 1, 31))
        assert result == Decimal("0")


class TestGetCategoryExpenseSum:
    def test_sums_all_transaction_types_for_category(self, repo, user, account, expense_cat):
        """Documents inconsistency: sums both debits and credits (unlike BudgetCalculationService)."""
        _txn(user, account, expense_cat, Decimal("100.00"), date(2024, 1, 10), "debit")
        _txn(user, account, expense_cat, Decimal("25.00"), date(2024, 1, 15), "credit")

        result = repo.get_category_expense_sum(user, expense_cat, date(2024, 1, 1), date(2024, 1, 31))
        assert result == Decimal("125.00")

    def test_returns_zero_when_no_transactions(self, repo, user, expense_cat):
        result = repo.get_category_expense_sum(user, expense_cat, date(2024, 1, 1), date(2024, 1, 31))
        assert result == Decimal("0")

    def test_filters_by_category(self, repo, user, account, expense_cat, expense_cat_2):
        _txn(user, account, expense_cat, Decimal("100.00"), date(2024, 1, 10))
        _txn(user, account, expense_cat_2, Decimal("75.00"), date(2024, 1, 10))

        result = repo.get_category_expense_sum(user, expense_cat, date(2024, 1, 1), date(2024, 1, 31))
        assert result == Decimal("100.00")


class TestGetNonessentialExpenseSum:
    def test_returns_same_as_total_expenses(self, repo, user, account, expense_cat):
        """Documents bug: nonessential filter is identical to total expense filter."""
        _txn(user, account, expense_cat, Decimal("200.00"), date(2024, 1, 10))

        total = repo.get_expense_sum_by_date_range(user, date(2024, 1, 1), date(2024, 1, 31))
        nonessential = repo.get_nonessential_expense_sum(user, date(2024, 1, 1), date(2024, 1, 31))
        assert total == nonessential


class TestGetActiveBudgetsForDateRange:
    def test_returns_overlapping_budgets(self, repo, user, expense_cat):
        budget = Budget.objects.create(
            user=user, name="Jan", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        BudgetCategory.objects.create(
            budget=budget, category=expense_cat, allocated_amount=Decimal("500.00"),
        )
        result = list(repo.get_active_budgets_for_date_range(user, date(2024, 1, 15), date(2024, 1, 20)))
        assert len(result) == 1
        assert result[0].name == "Jan"

    def test_excludes_inactive_budgets(self, repo, user):
        Budget.objects.create(
            user=user, name="Inactive", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31), is_active=False,
        )
        result = list(repo.get_active_budgets_for_date_range(user, date(2024, 1, 1), date(2024, 1, 31)))
        assert len(result) == 0

    def test_budget_starts_before_range(self, repo, user):
        Budget.objects.create(
            user=user, name="Early Start", period_type="monthly",
            start_date=date(2023, 12, 15), end_date=date(2024, 1, 15),
        )
        result = list(repo.get_active_budgets_for_date_range(user, date(2024, 1, 1), date(2024, 1, 31)))
        assert len(result) == 1

    def test_budget_ends_after_range(self, repo, user):
        Budget.objects.create(
            user=user, name="Late End", period_type="monthly",
            start_date=date(2024, 1, 15), end_date=date(2024, 2, 15),
        )
        result = list(repo.get_active_budgets_for_date_range(user, date(2024, 1, 1), date(2024, 1, 31)))
        assert len(result) == 1

    def test_budget_fully_outside_range(self, repo, user):
        Budget.objects.create(
            user=user, name="Outside", period_type="monthly",
            start_date=date(2024, 3, 1), end_date=date(2024, 3, 31),
        )
        result = list(repo.get_active_budgets_for_date_range(user, date(2024, 1, 1), date(2024, 1, 31)))
        assert len(result) == 0


class TestGetExpensesByCategory:
    def test_returns_grouped_by_category(self, repo, user, account, expense_cat, expense_cat_2):
        _txn(user, account, expense_cat, Decimal("200.00"), date(2024, 1, 10))
        _txn(user, account, expense_cat_2, Decimal("50.00"), date(2024, 1, 15))

        result = list(repo.get_expenses_by_category(user, date(2024, 1, 1), date(2024, 1, 31)))
        assert len(result) == 2
        assert result[0]["total"] > result[1]["total"]

    def test_respects_limit(self, repo, user, account, expense_cat, expense_cat_2):
        _txn(user, account, expense_cat, Decimal("200.00"), date(2024, 1, 10))
        _txn(user, account, expense_cat_2, Decimal("50.00"), date(2024, 1, 15))

        result = list(repo.get_expenses_by_category(user, date(2024, 1, 1), date(2024, 1, 31), limit=1))
        assert len(result) == 1


class TestGetExpenseYears:
    def test_returns_years_with_expenses(self, repo, user, account, expense_cat):
        _txn(user, account, expense_cat, Decimal("100.00"), date(2024, 6, 10))
        _txn(user, account, expense_cat, Decimal("50.00"), date(2023, 3, 15))

        result = repo.get_expense_years(user)
        assert 2024 in result
        assert 2023 in result

    def test_returns_empty_when_no_expenses(self, repo, user):
        result = repo.get_expense_years(user)
        assert result == []
