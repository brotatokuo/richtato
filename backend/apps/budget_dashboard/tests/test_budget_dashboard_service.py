"""Tests for Budget Dashboard Service."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock

import pytest

from apps.budget_dashboard.repositories import BudgetDashboardRepository
from apps.budget_dashboard.services import BudgetDashboardService


@pytest.fixture
def mock_repo():
    """Create a mock repository for testing."""
    return Mock(spec=BudgetDashboardRepository)


@pytest.fixture
def service(mock_repo):
    """Create a service instance with mock repository."""
    return BudgetDashboardService(mock_repo)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    return user


class TestBudgetDashboardService:
    """Test suite for BudgetDashboardService."""

    def test_get_expense_categories_data(self, service, mock_repo, mock_user):
        """Test expense categories data generation."""
        # Setup
        mock_repo.get_expenses_by_category.return_value = [
            {"category__name": "Food", "total": Decimal("100.00")},
            {"category__name": "Transport", "total": Decimal("50.00")},
        ]

        # Execute
        result = service.get_expense_categories_data(mock_user, year=2024, month=1)

        # Assert
        assert "labels" in result
        assert "datasets" in result
        assert len(result["labels"]) == 2
        assert result["labels"][0] == "Food"
        assert result["labels"][1] == "Transport"
        assert len(result["datasets"][0]["data"]) == 2

    def test_get_budget_progress(self, service, mock_repo, mock_user):
        """Test budget progress calculation."""
        # Setup
        mock_budget = Mock()
        mock_budget.category.name = "Food"
        mock_budget.amount = Decimal("200.00")

        mock_repo.get_active_budgets_for_date_range.return_value = [mock_budget]
        mock_repo.get_category_expense_sum.return_value = Decimal("150.00")

        # Execute
        result = service.get_budget_progress(mock_user, year=2024, month=1)

        # Assert
        assert "budgets" in result
        assert len(result["budgets"]) == 1
        assert result["budgets"][0]["category"] == "Food"
        assert result["budgets"][0]["budget"] == 200.00
        assert result["budgets"][0]["spent"] == 150.00
        assert result["budgets"][0]["percentage"] == 75

    def test_get_budget_rankings(self, service, mock_repo, mock_user):
        """Test budget rankings generation."""
        # Setup
        mock_budget1 = Mock()
        mock_budget1.category.name = "Food"
        mock_budget1.amount = Decimal("200.00")

        mock_budget2 = Mock()
        mock_budget2.category.name = "Transport"
        mock_budget2.amount = Decimal("100.00")

        mock_repo.get_active_budgets_for_date_range.return_value = [
            mock_budget1,
            mock_budget2,
        ]
        mock_repo.get_category_expense_sum.side_effect = [
            Decimal("180.00"),  # Food: 90%
            Decimal("80.00"),  # Transport: 80%
        ]

        # Execute
        result = service.get_budget_rankings(mock_user, 2024, 1)

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "Food"
        assert result[0]["percent"] == 90
        assert result[1]["name"] == "Transport"
        assert result[1]["percent"] == 80

    def test_get_budget_utilization(self, service, mock_repo, mock_user):
        """Test budget utilization calculation."""
        # Setup
        mock_budget = Mock()
        mock_budget.category.name = "Food"
        mock_budget.amount = Decimal("200.00")

        mock_repo.get_active_budgets_for_date_range.return_value = [mock_budget]
        mock_repo.get_category_expense_sum.return_value = Decimal("150.00")

        # Execute
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        result = service.get_budget_utilization(mock_user, start, end)

        # Assert
        assert result == "75.0%"

    def test_get_nonessential_spending_pct(self, service, mock_repo, mock_user):
        """Test non-essential spending percentage calculation."""
        # Setup
        mock_repo.get_expense_sum_by_date_range.return_value = Decimal("200.00")
        mock_repo.get_nonessential_expense_sum.return_value = Decimal("60.00")

        # Execute
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        result = service.get_nonessential_spending_pct(mock_user, start, end)

        # Assert
        assert result == 30.0

    def test_get_expense_years(self, service, mock_repo, mock_user):
        """Test getting expense years."""
        # Setup
        mock_repo.get_expense_years.return_value = [2024, 2023, 2022]

        # Execute
        result = service.get_expense_years(mock_user)

        # Assert
        assert result == [2024, 2023, 2022]
        mock_repo.get_expense_years.assert_called_once_with(mock_user)
