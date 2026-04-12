"""Tests for BudgetCalculationService."""

from datetime import date
from decimal import Decimal

import pytest
from apps.budget.models import Budget, BudgetCategory, BudgetProgress
from apps.budget.services.budget_calculation_service import BudgetCalculationService
from apps.budget.tests.conftest import create_transaction


@pytest.fixture
def calc_service():
    return BudgetCalculationService()


class TestCalculateCategoryProgress:
    def test_counts_only_debits_in_date_range(
        self, calc_service, user, account, budget, budget_category, expense_category
    ):
        create_transaction(user, account, expense_category, Decimal("50.00"), date(2024, 1, 5))
        create_transaction(user, account, expense_category, Decimal("30.00"), date(2024, 1, 15))

        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["spent_amount"] == Decimal("80.00")
        assert result["transaction_count"] == 2

    def test_ignores_credit_transactions(
        self, calc_service, user, account, budget, budget_category, expense_category
    ):
        create_transaction(user, account, expense_category, Decimal("100.00"), date(2024, 1, 5))
        create_transaction(
            user, account, expense_category, Decimal("25.00"), date(2024, 1, 10),
            transaction_type="credit",
        )

        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["spent_amount"] == Decimal("100.00")

    def test_ignores_transactions_outside_date_range(
        self, calc_service, user, account, budget, budget_category, expense_category
    ):
        create_transaction(user, account, expense_category, Decimal("100.00"), date(2024, 1, 15))
        create_transaction(user, account, expense_category, Decimal("50.00"), date(2023, 12, 31))
        create_transaction(user, account, expense_category, Decimal("50.00"), date(2024, 2, 1))

        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["spent_amount"] == Decimal("100.00")

    def test_ignores_transactions_in_different_category(
        self, calc_service, user, account, budget, budget_category, expense_category, expense_category_2
    ):
        create_transaction(user, account, expense_category, Decimal("100.00"), date(2024, 1, 10))
        create_transaction(user, account, expense_category_2, Decimal("75.00"), date(2024, 1, 10))

        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["spent_amount"] == Decimal("100.00")

    def test_uses_total_available_with_rollover(
        self, calc_service, user, account, budget, expense_category
    ):
        bc = BudgetCategory.objects.create(
            budget=budget, category=expense_category,
            allocated_amount=Decimal("500.00"),
            rollover_enabled=True, rollover_amount=Decimal("100.00"),
        )
        create_transaction(user, account, expense_category, Decimal("550.00"), date(2024, 1, 10))

        result = calc_service.calculate_category_progress(
            bc, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["total_available"] == Decimal("600.00")
        assert result["remaining_amount"] == Decimal("50.00")
        assert result["is_over_budget"] is False

    def test_status_on_track(self, calc_service, user, account, budget, budget_category, expense_category):
        create_transaction(user, account, expense_category, Decimal("100.00"), date(2024, 1, 10))

        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["status"] == "on_track"

    def test_status_caution(self, calc_service, user, account, budget, budget_category, expense_category):
        create_transaction(user, account, expense_category, Decimal("400.00"), date(2024, 1, 10))

        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["status"] == "caution"

    def test_status_warning(self, calc_service, user, account, budget, budget_category, expense_category):
        create_transaction(user, account, expense_category, Decimal("475.00"), date(2024, 1, 10))

        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["status"] == "warning"

    def test_status_over_budget(self, calc_service, user, account, budget, budget_category, expense_category):
        create_transaction(user, account, expense_category, Decimal("600.00"), date(2024, 1, 10))

        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["status"] == "over_budget"
        assert result["is_over_budget"] is True

    def test_zero_spent_returns_on_track(self, calc_service, budget_category):
        result = calc_service.calculate_category_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result["spent_amount"] == Decimal("0")
        assert result["status"] == "on_track"
        assert result["remaining_amount"] == Decimal("500.00")


class TestCalculateBudgetProgress:
    def test_aggregates_across_categories(
        self, calc_service, user, account, budget, expense_category, expense_category_2
    ):
        BudgetCategory.objects.create(
            budget=budget, category=expense_category, allocated_amount=Decimal("500.00"),
        )
        BudgetCategory.objects.create(
            budget=budget, category=expense_category_2, allocated_amount=Decimal("300.00"),
        )
        create_transaction(user, account, expense_category, Decimal("200.00"), date(2024, 1, 10))
        create_transaction(user, account, expense_category_2, Decimal("100.00"), date(2024, 1, 15))

        result = calc_service.calculate_budget_progress(budget)

        assert result["totals"]["allocated"] == Decimal("800.00")
        assert result["totals"]["spent"] == Decimal("300.00")
        assert result["totals"]["remaining"] == Decimal("500.00")
        assert len(result["categories"]) == 2

    def test_percentage_uses_total_available(
        self, calc_service, user, account, budget, expense_category
    ):
        BudgetCategory.objects.create(
            budget=budget, category=expense_category,
            allocated_amount=Decimal("400.00"),
            rollover_amount=Decimal("100.00"),
        )
        create_transaction(user, account, expense_category, Decimal("250.00"), date(2024, 1, 10))

        result = calc_service.calculate_budget_progress(budget)
        assert result["totals"]["allocated"] == Decimal("500.00")
        assert result["totals"]["percentage_used"] == Decimal("50.0")

    def test_empty_budget_returns_zero_totals(self, calc_service, budget):
        result = calc_service.calculate_budget_progress(budget)
        assert result["totals"]["allocated"] == Decimal("0")
        assert result["totals"]["spent"] == Decimal("0")
        assert result["categories"] == []


class TestUpdateCachedProgress:
    def test_creates_progress_record(
        self, calc_service, user, account, budget, budget_category, expense_category
    ):
        create_transaction(user, account, expense_category, Decimal("75.00"), date(2024, 1, 10))

        progress = calc_service.update_cached_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert progress.id is not None
        assert progress.spent_amount == Decimal("75.00")
        assert progress.transaction_count == 1

    def test_updates_existing_record(
        self, calc_service, user, account, budget, budget_category, expense_category
    ):
        create_transaction(user, account, expense_category, Decimal("50.00"), date(2024, 1, 5))
        calc_service.update_cached_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )

        create_transaction(user, account, expense_category, Decimal("25.00"), date(2024, 1, 20))
        progress = calc_service.update_cached_progress(
            budget_category, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert progress.spent_amount == Decimal("75.00")
        assert progress.transaction_count == 2
        assert BudgetProgress.objects.filter(budget_category=budget_category).count() == 1
