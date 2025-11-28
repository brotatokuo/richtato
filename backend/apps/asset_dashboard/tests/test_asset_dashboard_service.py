"""Tests for Asset Dashboard Service."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from apps.asset_dashboard.repositories import AssetDashboardRepository
from apps.asset_dashboard.services import AssetDashboardService


@pytest.fixture
def mock_repo():
    """Create a mock repository for testing."""
    return Mock(spec=AssetDashboardRepository)


@pytest.fixture
def service(mock_repo):
    """Create a service instance with mock repository."""
    return AssetDashboardService(mock_repo)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    return user


class TestAssetDashboardService:
    """Test suite for AssetDashboardService."""

    def test_get_cash_flow_data_6m(self, service, mock_repo, mock_user):
        """Test cash flow data generation for 6 months."""
        # Setup
        mock_repo.get_income_sum_by_date_range.return_value = Decimal("1000.00")
        mock_repo.get_expense_sum_by_date_range.return_value = Decimal("600.00")

        # Execute
        result = service.get_cash_flow_data(mock_user, period="6m")

        # Assert
        assert "labels" in result
        assert "datasets" in result
        assert len(result["datasets"]) == 3  # Net Cash Flow, Income, Expenses

    def test_get_income_expenses_data(self, service, mock_repo, mock_user):
        """Test income vs expenses data generation."""
        # Setup
        mock_repo.get_income_sum_by_date_range.return_value = Decimal("1000.00")
        mock_repo.get_expense_sum_by_date_range.return_value = Decimal("600.00")

        # Execute
        result = service.get_income_expenses_data(mock_user)

        # Assert
        assert "labels" in result
        assert "datasets" in result
        assert len(result["datasets"]) == 2  # Income and Expenses

    def test_get_savings_data(self, service, mock_repo, mock_user):
        """Test savings data generation."""
        # Setup
        mock_repo.get_income_sum_by_date_range.return_value = Decimal("1000.00")
        mock_repo.get_expense_sum_by_date_range.return_value = Decimal("600.00")

        # Execute
        result = service.get_savings_data(mock_user)

        # Assert
        assert "labels" in result
        assert "datasets" in result
        assert len(result["datasets"]) == 2  # Total Savings and Monthly Savings

    def test_get_dashboard_metrics(self, service, mock_repo, mock_user):
        """Test dashboard metrics calculation."""
        # Setup
        mock_repo.get_networth.return_value = Decimal("10000.00")
        mock_repo.get_income_sum_by_date_range.return_value = Decimal("2000.00")
        mock_repo.get_expense_sum_by_date_range.return_value = Decimal("1200.00")
        mock_repo.get_user_accounts.return_value = []

        # Execute
        result = service.get_dashboard_metrics(mock_user)

        # Assert
        assert "networth" in result
        assert "networth_growth" in result
        assert "savings_rate" in result
        assert "savings_rate_context" in result
        assert "income_sum" in result
        assert "expense_sum" in result

    def test_calculate_savings_rate_context_below_average(
        self, service, mock_repo, mock_user
    ):
        """Test savings rate context for below average rate."""
        # Execute
        context, css_class = service._calculate_savings_rate_context("5%")

        # Assert
        assert context == "Below average"
        assert css_class == "negative"

    def test_calculate_savings_rate_context_average(
        self, service, mock_repo, mock_user
    ):
        """Test savings rate context for average rate."""
        # Execute
        context, css_class = service._calculate_savings_rate_context("15%")

        # Assert
        assert context == "Average"
        assert css_class == ""

    def test_calculate_savings_rate_context_good(self, service, mock_repo, mock_user):
        """Test savings rate context for good rate."""
        # Execute
        context, css_class = service._calculate_savings_rate_context("25%")

        # Assert
        assert context == "Good"
        assert css_class == "positive"

    def test_calculate_savings_rate_context_above_average(
        self, service, mock_repo, mock_user
    ):
        """Test savings rate context for above average rate."""
        # Execute
        context, css_class = service._calculate_savings_rate_context("35%")

        # Assert
        assert context == "Above average"
        assert css_class == "positive"

    def test_calculate_networth_growth(self, service, mock_repo, mock_user):
        """Test networth growth calculation."""
        # Setup
        mock_repo.get_networth.return_value = Decimal("11000.00")
        mock_account = Mock()
        mock_repo.get_user_accounts.return_value = [mock_account]
        mock_repo.get_account_balance_before_date.return_value = Decimal("10000.00")

        # Execute
        result = service._calculate_networth_growth(mock_user)

        # Assert
        assert "%" in result
        assert "this month" in result
