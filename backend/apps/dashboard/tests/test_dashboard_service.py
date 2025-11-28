"""Unit tests for DashboardService - no database access."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from django.test import SimpleTestCase

from apps.dashboard.services import DashboardService


class DashboardServiceTestCase(SimpleTestCase):
    """Unit tests for DashboardService with mocked repository (NO DB)."""

    def setUp(self):
        """Set up test fixtures with mocked repository."""
        self.mock_dashboard_repo = Mock()
        self.service = DashboardService(self.mock_dashboard_repo)

    def test_calculate_savings_rate_context_below_average(self):
        """Test savings rate context for below average rate."""
        context, css_class = self.service._calculate_savings_rate_context("5%")
        self.assertEqual(context, "Below average")
        self.assertEqual(css_class, "negative")

    def test_calculate_savings_rate_context_average(self):
        """Test savings rate context for average rate."""
        context, css_class = self.service._calculate_savings_rate_context("15%")
        self.assertEqual(context, "Average")
        self.assertEqual(css_class, "")

    def test_calculate_savings_rate_context_good(self):
        """Test savings rate context for good rate."""
        context, css_class = self.service._calculate_savings_rate_context("25%")
        self.assertEqual(context, "Good")
        self.assertEqual(css_class, "positive")

    def test_calculate_savings_rate_context_above_average(self):
        """Test savings rate context for above average rate."""
        context, css_class = self.service._calculate_savings_rate_context("35%")
        self.assertEqual(context, "Above average")
        self.assertEqual(css_class, "positive")

    def test_determine_date_range_with_dates(self):
        """Test date range determination with explicit dates."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        result_start, result_end = self.service._determine_date_range(
            start, end, None, None
        )

        self.assertEqual(result_start, start)
        self.assertEqual(result_end, end)

    def test_determine_date_range_with_year_month(self):
        """Test date range determination with year and month."""
        result_start, result_end = self.service._determine_date_range(
            None, None, 2024, 2
        )

        self.assertEqual(result_start, date(2024, 2, 1))
        self.assertEqual(result_end, date(2024, 2, 29))  # Leap year

    def test_determine_date_range_defaults_to_current_month(self):
        """Test date range determination defaults to current month."""
        result_start, result_end = self.service._determine_date_range(
            None, None, None, None
        )

        today = date.today()
        expected_start = today.replace(day=1)

        self.assertEqual(result_start.year, expected_start.year)
        self.assertEqual(result_start.month, expected_start.month)
        self.assertEqual(result_start.day, 1)

    def test_get_expense_years(self):
        """Test getting expense years."""
        mock_user = Mock()

        # Mock repository
        self.mock_dashboard_repo.get_expense_years.return_value = [2022, 2023, 2024]

        # Call service
        result = self.service.get_expense_years(mock_user)

        # Assert result
        self.assertEqual(result, [2022, 2023, 2024])
        self.mock_dashboard_repo.get_expense_years.assert_called_once_with(mock_user)

    def test_get_cash_flow_data_6m_period(self):
        """Test cash flow data generation for 6 month period."""
        mock_user = Mock()

        # Mock repository methods
        self.mock_dashboard_repo.get_income_sum_by_date_range.return_value = Decimal(
            "5000.00"
        )
        self.mock_dashboard_repo.get_expense_sum_by_date_range.return_value = Decimal(
            "3000.00"
        )

        # Call service
        result = self.service.get_cash_flow_data(mock_user, "6m")

        # Assert structure
        self.assertIn("labels", result)
        self.assertIn("datasets", result)
        self.assertEqual(len(result["datasets"]), 3)  # Net, Income, Expenses

        # Assert datasets have correct labels
        dataset_labels = [ds["label"] for ds in result["datasets"]]
        self.assertIn("Net Cash Flow", dataset_labels)
        self.assertIn("Income", dataset_labels)
        self.assertIn("Expenses", dataset_labels)

    def test_get_expense_categories_data(self):
        """Test expense categories data generation."""
        mock_user = Mock()

        # Mock repository
        self.mock_dashboard_repo.get_expenses_by_category.return_value = [
            {"category__name": "Food", "total": Decimal("500.00")},
            {"category__name": "Transport", "total": Decimal("300.00")},
        ]

        # Call service
        result = self.service.get_expense_categories_data(
            mock_user, date(2024, 1, 1), date(2024, 1, 31)
        )

        # Assert structure
        self.assertIn("labels", result)
        self.assertIn("datasets", result)
        self.assertEqual(len(result["labels"]), 2)
        self.assertEqual(result["labels"][0], "Food")
        self.assertEqual(result["labels"][1], "Transport")

    def test_get_dashboard_metrics(self):
        """Test dashboard metrics calculation."""
        mock_user = Mock()

        # Mock repository methods
        self.mock_dashboard_repo.get_networth.return_value = Decimal("50000.00")
        self.mock_dashboard_repo.get_income_sum_by_date_range.return_value = Decimal(
            "5000.00"
        )
        self.mock_dashboard_repo.get_expense_sum_by_date_range.return_value = Decimal(
            "3000.00"
        )
        self.mock_dashboard_repo.get_nonessential_expense_sum.return_value = Decimal(
            "500.00"
        )
        self.mock_dashboard_repo.get_active_budgets_for_date_range.return_value = []
        self.mock_dashboard_repo.get_user_accounts.return_value = []

        # Call service
        result = self.service.get_dashboard_metrics(mock_user)

        # Assert structure
        self.assertIn("networth", result)
        self.assertIn("networth_growth", result)
        self.assertIn("expense_sum", result)
        self.assertIn("income_sum", result)
        self.assertIn("savings_rate", result)
        self.assertIn("savings_rate_context", result)

        # Assert savings rate is calculated correctly
        # Income 5000, Expense 3000 = 2000 savings = 40%
        self.assertEqual(result["savings_rate"], "40.0%")
        self.assertEqual(result["savings_rate_context"], "Above average")

    def test_calculate_budget_utilization_no_budgets(self):
        """Test budget utilization with no budgets."""
        mock_user = Mock()
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        # Mock no budgets
        self.mock_dashboard_repo.get_active_budgets_for_date_range.return_value = []

        # Call private method
        result = self.service._calculate_budget_utilization(
            mock_user, start_date, end_date
        )

        # Assert N/A returned
        self.assertEqual(result, "N/A")
