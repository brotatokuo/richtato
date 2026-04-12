"""Tests for BudgetService."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from apps.budget.models import Budget, BudgetCategory
from apps.budget.services.budget_service import BudgetService
from apps.transaction.models import TransactionCategory


@pytest.fixture
def service():
    return BudgetService()


class TestCreateBudget:
    def test_creates_budget_with_basic_fields(self, service, user):
        budget = service.create_budget(
            user=user,
            name="March Budget",
            period_type="monthly",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31),
        )
        assert budget.id is not None
        assert budget.name == "March Budget"
        assert budget.period_type == "monthly"
        assert budget.start_date == date(2024, 3, 1)
        assert budget.end_date == date(2024, 3, 31)
        assert budget.is_active is True
        assert budget.user == user

    def test_creates_budget_with_categories(self, service, user, expense_category, expense_category_2):
        categories_data = [
            {"category_id": expense_category.id, "allocated_amount": Decimal("300.00")},
            {"category_id": expense_category_2.id, "allocated_amount": Decimal("150.00")},
        ]
        budget = service.create_budget(
            user=user,
            name="With Categories",
            period_type="monthly",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31),
            categories_data=categories_data,
        )
        bc_list = list(budget.budget_categories.all())
        assert len(bc_list) == 2
        amounts = {bc.category.name: bc.allocated_amount for bc in bc_list}
        assert amounts["Test Groceries"] == Decimal("300.00")
        assert amounts["Test Transport"] == Decimal("150.00")

    def test_creates_budget_category_with_rollover_enabled(self, service, user, expense_category):
        categories_data = [
            {
                "category_id": expense_category.id,
                "allocated_amount": Decimal("200.00"),
                "rollover_enabled": True,
            },
        ]
        budget = service.create_budget(
            user=user,
            name="Rollover Budget",
            period_type="monthly",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31),
            categories_data=categories_data,
        )
        bc = budget.budget_categories.first()
        assert bc.rollover_enabled is True

    def test_raises_on_invalid_category_id(self, service, user):
        categories_data = [
            {"category_id": 99999, "allocated_amount": Decimal("100.00")},
        ]
        with pytest.raises(TransactionCategory.DoesNotExist):
            service.create_budget(
                user=user,
                name="Bad Category",
                period_type="monthly",
                start_date=date(2024, 3, 1),
                end_date=date(2024, 3, 31),
                categories_data=categories_data,
            )


class TestCreateMonthlyBudget:
    def test_sets_correct_date_range(self, service, user):
        budget = service.create_monthly_budget(
            user=user, name="Feb 2024", year=2024, month=2, categories_data=[]
        )
        assert budget.start_date == date(2024, 2, 1)
        assert budget.end_date == date(2024, 2, 29)  # 2024 is a leap year
        assert budget.period_type == "monthly"

    def test_handles_december(self, service, user):
        budget = service.create_monthly_budget(
            user=user, name="Dec 2024", year=2024, month=12, categories_data=[]
        )
        assert budget.start_date == date(2024, 12, 1)
        assert budget.end_date == date(2024, 12, 31)


class TestGetUserBudgets:
    def test_returns_only_active_budgets(self, service, user):
        Budget.objects.create(
            user=user, name="Active", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31), is_active=True,
        )
        Budget.objects.create(
            user=user, name="Inactive", period_type="monthly",
            start_date=date(2024, 2, 1), end_date=date(2024, 2, 29), is_active=False,
        )
        result = service.get_user_budgets(user, active_only=True)
        assert len(result) == 1
        assert result[0].name == "Active"

    def test_returns_all_when_active_only_false(self, service, user):
        Budget.objects.create(
            user=user, name="Active", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31), is_active=True,
        )
        Budget.objects.create(
            user=user, name="Inactive", period_type="monthly",
            start_date=date(2024, 2, 1), end_date=date(2024, 2, 29), is_active=False,
        )
        result = service.get_user_budgets(user, active_only=False)
        assert len(result) == 2

    def test_returns_only_own_budgets(self, service, user, other_user):
        Budget.objects.create(
            user=user, name="Mine", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        Budget.objects.create(
            user=other_user, name="Theirs", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        result = service.get_user_budgets(user)
        assert len(result) == 1
        assert result[0].name == "Mine"


class TestGetBudgetById:
    def test_returns_budget_for_owner(self, service, user, budget):
        result = service.get_budget_by_id(budget.id, user)
        assert result is not None
        assert result.id == budget.id

    def test_returns_none_for_wrong_user(self, service, other_user, budget):
        result = service.get_budget_by_id(budget.id, other_user)
        assert result is None

    def test_returns_none_for_nonexistent(self, service, user):
        result = service.get_budget_by_id(99999, user)
        assert result is None


class TestGetCurrentBudget:
    def test_returns_budget_covering_today(self, service, user):
        today = date.today()
        Budget.objects.create(
            user=user, name="Current", period_type="monthly",
            start_date=today - timedelta(days=15),
            end_date=today + timedelta(days=15),
        )
        result = service.get_current_budget(user)
        assert result is not None
        assert result.name == "Current"

    def test_returns_none_when_no_budget_covers_today(self, service, user):
        Budget.objects.create(
            user=user, name="Past", period_type="monthly",
            start_date=date(2020, 1, 1), end_date=date(2020, 1, 31),
        )
        result = service.get_current_budget(user)
        assert result is None

    def test_returns_none_when_inactive(self, service, user):
        today = date.today()
        Budget.objects.create(
            user=user, name="Inactive Current", period_type="monthly",
            start_date=today - timedelta(days=15),
            end_date=today + timedelta(days=15),
            is_active=False,
        )
        result = service.get_current_budget(user)
        assert result is None


class TestDeleteBudget:
    def test_soft_deletes_budget(self, service, budget):
        result = service.delete_budget(budget)
        assert result is True
        budget.refresh_from_db()
        assert budget.is_active is False

    def test_budget_still_exists_in_db(self, service, budget):
        service.delete_budget(budget)
        assert Budget.objects.filter(id=budget.id).exists()


class TestDuplicateBudget:
    def test_creates_new_budget_with_same_categories(self, service, budget, budget_category):
        new_budget = service.duplicate_budget(
            budget,
            new_start_date=date(2024, 2, 1),
            new_end_date=date(2024, 2, 29),
        )
        assert new_budget.id != budget.id
        assert new_budget.start_date == date(2024, 2, 1)
        assert new_budget.end_date == date(2024, 2, 29)
        assert new_budget.period_type == budget.period_type

        new_categories = list(new_budget.budget_categories.all())
        assert len(new_categories) == 1
        assert new_categories[0].allocated_amount == Decimal("500.00")
        assert new_categories[0].category == budget_category.category

    def test_copies_rollover_enabled_but_not_rollover_amount(self, service, budget, expense_category):
        BudgetCategory.objects.create(
            budget=budget, category=expense_category,
            allocated_amount=Decimal("200.00"),
            rollover_enabled=True, rollover_amount=Decimal("50.00"),
        )
        new_budget = service.duplicate_budget(
            budget, new_start_date=date(2024, 2, 1), new_end_date=date(2024, 2, 29),
        )
        new_bc = new_budget.budget_categories.first()
        assert new_bc.rollover_enabled is True
        assert new_bc.rollover_amount == Decimal("0")

    def test_uses_copy_suffix_when_no_name(self, service, budget):
        new_budget = service.duplicate_budget(
            budget, new_start_date=date(2024, 2, 1), new_end_date=date(2024, 2, 29),
        )
        assert new_budget.name == "January 2024 (Copy)"

    def test_uses_provided_name(self, service, budget):
        new_budget = service.duplicate_budget(
            budget, new_start_date=date(2024, 2, 1), new_end_date=date(2024, 2, 29),
            new_name="February 2024",
        )
        assert new_budget.name == "February 2024"


class TestAddBudgetCategory:
    def test_adds_category_to_budget(self, service, budget, expense_category):
        bc = service.add_budget_category(
            budget=budget, category=expense_category, allocated_amount=Decimal("250.00"),
        )
        assert bc.id is not None
        assert bc.budget == budget
        assert bc.category == expense_category
        assert bc.allocated_amount == Decimal("250.00")
        assert bc.rollover_enabled is False


class TestUpdateBudgetCategory:
    def test_updates_allocated_amount(self, service, budget_category):
        updated = service.update_budget_category(
            budget_category, allocated_amount=Decimal("750.00"),
        )
        updated.refresh_from_db()
        assert updated.allocated_amount == Decimal("750.00")

    def test_updates_rollover_enabled(self, service, budget_category):
        updated = service.update_budget_category(
            budget_category, rollover_enabled=True,
        )
        updated.refresh_from_db()
        assert updated.rollover_enabled is True
