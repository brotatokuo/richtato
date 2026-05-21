"""Tests for category settings budget sync behavior."""

from datetime import date
from decimal import Decimal

import pytest

from apps.budget.models import Budget, BudgetCategory
from apps.richtato_user.models import User
from apps.richtato_user.services.category_settings_service import CategorySettingsService
from apps.transaction.models import TransactionCategory


@pytest.fixture
def user(db):
    return User.objects.create_user(username="cat_settings_user", password="testpass123")


@pytest.fixture
def category(user):
    category, _ = TransactionCategory.objects.get_or_create(
        user=user,
        slug="groceries",
        defaults={
            "name": "Groceries",
            "type": "expense",
        },
    )
    return category


def test_sync_budgets_uses_payload_period(user, category):
    service = CategorySettingsService()

    service.update_settings(
        user,
        {
            "budgets": {
                "groceries": {
                    "amount": 450,
                    "start_date": "2024-03-01",
                    "end_date": "2024-03-31",
                }
            }
        },
    )

    budget = Budget.objects.get(user=user, start_date=date(2024, 3, 1), end_date=date(2024, 3, 31))
    budget_category = BudgetCategory.objects.get(budget=budget, category=category)

    assert budget_category.allocated_amount == Decimal("450")


def test_sync_budgets_can_remove_from_payload_period(user, category):
    budget = Budget.objects.create(
        user=user,
        name="Monthly Budget - March 2024",
        period_type="monthly",
        start_date=date(2024, 3, 1),
        end_date=date(2024, 3, 31),
    )
    BudgetCategory.objects.create(
        budget=budget,
        category=category,
        allocated_amount=Decimal("450"),
    )

    service = CategorySettingsService()
    service.update_settings(
        user,
        {
            "budgets": {
                "groceries": {
                    "amount": None,
                    "start_date": "2024-03-01",
                    "end_date": "2024-03-31",
                }
            }
        },
    )

    assert not BudgetCategory.objects.filter(budget=budget, category=category).exists()
