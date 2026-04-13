"""Tests for household-level budget behavior."""

from datetime import date

import pytest

from apps.budget.models import Budget
from apps.budget.services.budget_service import BudgetService
from apps.household.models import Household, HouseholdMember
from apps.richtato_user.models import User


@pytest.fixture
def user_a(db):
    return User.objects.create_user(username="bud_a", password="testpass123")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(username="bud_b", password="testpass123")


@pytest.fixture
def household_both(user_a, user_b):
    h = Household.objects.create(name="Test", created_by=user_a)
    HouseholdMember.objects.create(household=h, user=user_a)
    HouseholdMember.objects.create(household=h, user=user_b)
    return h


@pytest.fixture
def service():
    return BudgetService()


class TestHouseholdBudget:
    def test_personal_scope_excludes_household_budgets(self, service, user_a):
        Budget.objects.create(
            user=user_a, name="Personal", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        Budget.objects.create(
            user=user_a, name="Household", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            is_household=True,
        )
        result = service.get_user_budgets(user_a)
        names = [b.name for b in result]
        assert "Personal" in names
        assert "Household" in names  # get_user_budgets returns all user's budgets

    def test_household_scope_returns_household_budgets(self, service, user_a, user_b, household_both):
        Budget.objects.create(
            user=user_a, name="Personal", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        Budget.objects.create(
            user=user_a, name="Household Budget", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            is_household=True,
        )
        result = service.get_household_budgets([user_a.id, user_b.id])
        assert len(result) == 1
        assert result[0].name == "Household Budget"

    def test_household_budgets_only_include_is_household_true(self, service, user_a, user_b, household_both):
        Budget.objects.create(
            user=user_a, name="Not HH", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            is_household=False,
        )
        Budget.objects.create(
            user=user_b, name="HH Budget", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            is_household=True,
        )
        result = service.get_household_budgets([user_a.id, user_b.id])
        assert len(result) == 1
        assert result[0].name == "HH Budget"
