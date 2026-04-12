"""Tests for Budget Dashboard Service."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

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
        mock_budget_category = Mock()
        mock_budget_category.category.name = "Food"
        mock_budget_category.allocated_amount = Decimal("200.00")

        mock_budget = Mock()
        mock_budget.budget_categories.all.return_value = [mock_budget_category]

        mock_repo.get_active_budgets_for_date_range.return_value = [mock_budget]
        mock_repo.get_category_expense_sum.return_value = Decimal("150.00")

        result = service.get_budget_progress(mock_user, year=2024, month=1)

        assert "budgets" in result
        assert len(result["budgets"]) == 1
        assert result["budgets"][0]["category"] == "Food"
        assert result["budgets"][0]["budget"] == 200.00
        assert result["budgets"][0]["spent"] == 150.00
        assert result["budgets"][0]["percentage"] == 75

    def test_get_budget_rankings(self, service, mock_repo, mock_user):
        """Test budget rankings generation."""
        mock_bc_food = Mock()
        mock_bc_food.category.name = "Food"
        mock_bc_food.allocated_amount = Decimal("200.00")

        mock_bc_transport = Mock()
        mock_bc_transport.category.name = "Transport"
        mock_bc_transport.allocated_amount = Decimal("100.00")

        mock_budget = Mock()
        mock_budget.budget_categories.all.return_value = [mock_bc_food, mock_bc_transport]

        mock_repo.get_active_budgets_for_date_range.return_value = [mock_budget]
        mock_repo.get_category_expense_sum.side_effect = [
            Decimal("180.00"),  # Food: 90%
            Decimal("80.00"),  # Transport: 80%
        ]

        result = service.get_budget_rankings(mock_user, 2024, 1)

        assert len(result) == 2
        assert result[0]["name"] == "Food"
        assert result[0]["percent"] == 90
        assert result[1]["name"] == "Transport"
        assert result[1]["percent"] == 80

    def test_get_budget_utilization(self, service, mock_repo, mock_user):
        """Test budget utilization calculation with multiple budgets."""
        mock_bc_food = Mock()
        mock_bc_food.category.name = "Food"
        mock_bc_food.allocated_amount = Decimal("200.00")

        mock_bc_transport = Mock()
        mock_bc_transport.category.name = "Transport"
        mock_bc_transport.allocated_amount = Decimal("100.00")

        mock_budget = Mock()
        mock_budget.budget_categories.all.return_value = [mock_bc_food, mock_bc_transport]

        mock_repo.get_active_budgets_for_date_range.return_value = [mock_budget]

        mock_repo.get_category_expense_sum.side_effect = [
            Decimal("150.00"),
            Decimal("50.00"),
        ]

        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        result = service.get_budget_utilization(mock_user, start, end)

        assert result == "66.7%"

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


class TestBudgetProgressMultiMonth:
    """Tests for get_budget_progress_multi_month."""

    def test_returns_correct_number_of_months(self, service, mock_repo, mock_user):
        mock_repo.get_active_budgets_for_date_range.return_value = []

        result = service.get_budget_progress_multi_month(mock_user, months=3)

        assert len(result["monthly_data"]) == 3
        assert result["months_requested"] == 3

    def test_months_ordered_chronologically(self, service, mock_repo, mock_user):
        mock_repo.get_active_budgets_for_date_range.return_value = []

        result = service.get_budget_progress_multi_month(mock_user, months=6)

        months = result["monthly_data"]
        for i in range(len(months) - 1):
            current = date(months[i]["year"], months[i]["month"], 1)
            nxt = date(months[i + 1]["year"], months[i + 1]["month"], 1)
            assert current < nxt

    def test_each_month_has_expected_fields(self, service, mock_repo, mock_user):
        mock_repo.get_active_budgets_for_date_range.return_value = []

        result = service.get_budget_progress_multi_month(mock_user, months=1)

        month_data = result["monthly_data"][0]
        assert "year" in month_data
        assert "month" in month_data
        assert "month_name" in month_data
        assert "total_budget" in month_data
        assert "total_spent" in month_data
        assert "percentage" in month_data
        assert "categories" in month_data
        assert "start_date" in month_data
        assert "end_date" in month_data


class TestDetermineDateRange:
    """Tests for _determine_date_range."""

    def test_returns_explicit_dates_when_both_provided(self, service):
        start = date(2024, 3, 1)
        end = date(2024, 3, 31)
        result_start, result_end = service._determine_date_range(start, end, None, None)
        assert result_start == start
        assert result_end == end

    def test_falls_back_to_year_month(self, service):
        result_start, result_end = service._determine_date_range(None, None, 2024, 2)
        assert result_start == date(2024, 2, 1)
        assert result_end == date(2024, 2, 29)

    def test_falls_back_to_current_month(self, service):
        today = date.today()
        result_start, result_end = service._determine_date_range(None, None, None, None)
        assert result_start.year == today.year
        assert result_start.month == today.month
        assert result_start.day == 1


class TestCalculateBudgetDiffMessage:
    """Tests for _calculate_budget_diff_message."""

    def test_under_budget_message(self, service):
        result = service._calculate_budget_diff_message(Decimal("-50.00"), 75)
        assert "left" in result
        assert "75%" in result

    def test_over_budget_message(self, service):
        result = service._calculate_budget_diff_message(Decimal("30.00"), 115)
        assert "over" in result
        assert "115%" in result

    def test_exact_budget_message(self, service):
        result = service._calculate_budget_diff_message(Decimal("0.00"), 100)
        assert "left" in result
        assert "100%" in result
