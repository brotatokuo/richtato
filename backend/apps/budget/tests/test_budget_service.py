"""Unit tests for BudgetService - no database access."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from django.test import SimpleTestCase

from apps.budget.services import BudgetService


class BudgetServiceTestCase(SimpleTestCase):
    """Unit tests for BudgetService with mocked repositories (NO DB)."""

    def setUp(self):
        """Set up test fixtures with mocked repositories."""
        self.mock_budget_repo = Mock()
        self.mock_expense_repo = Mock()
        self.mock_category_repo = Mock()
        self.service = BudgetService(
            self.mock_budget_repo, self.mock_expense_repo, self.mock_category_repo
        )

    def test_validate_budget_dates_valid(self):
        """Test date validation with valid dates."""
        valid, error = self.service.validate_budget_dates(
            date(2024, 1, 1), date(2024, 12, 31)
        )
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_budget_dates_no_end(self):
        """Test date validation with no end date (infinite budget)."""
        valid, error = self.service.validate_budget_dates(date(2024, 1, 1), None)
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_budget_dates_invalid(self):
        """Test date validation with start >= end."""
        valid, error = self.service.validate_budget_dates(
            date(2024, 12, 31), date(2024, 1, 1)
        )
        self.assertFalse(valid)
        self.assertIn("before", error)

    def test_ranges_overlap_true(self):
        """Test range overlap detection when ranges overlap."""
        # Range 1: Jan 1 - Mar 31
        # Range 2: Feb 1 - Apr 30
        # These overlap in February and March
        overlaps = self.service._ranges_overlap(
            date(2024, 1, 1),
            date(2024, 3, 31),
            date(2024, 2, 1),
            date(2024, 4, 30),
        )
        self.assertTrue(overlaps)

    def test_ranges_overlap_false(self):
        """Test range overlap detection when ranges don't overlap."""
        # Range 1: Jan 1 - Jan 31
        # Range 2: Feb 1 - Feb 28
        # These don't overlap
        overlaps = self.service._ranges_overlap(
            date(2024, 1, 1), date(2024, 1, 31), date(2024, 2, 1), date(2024, 2, 28)
        )
        self.assertFalse(overlaps)

    def test_ranges_overlap_with_none_end_date(self):
        """Test range overlap with infinite end date."""
        # Range 1: Jan 1 - infinite
        # Range 2: Feb 1 - Feb 28
        # These overlap
        overlaps = self.service._ranges_overlap(
            date(2024, 1, 1), None, date(2024, 2, 1), date(2024, 2, 28)
        )
        self.assertTrue(overlaps)

    def test_create_budget_success(self):
        """Test creating a budget successfully."""
        mock_user = Mock()
        mock_category = Mock()
        mock_category.id = 1

        # Mock category repository
        self.mock_category_repo.get_by_id.return_value = mock_category

        # Mock no overlaps
        self.mock_budget_repo.get_overlapping_budgets.return_value = []

        # Mock budget creation
        mock_budget = Mock()
        mock_budget.id = 1
        self.mock_budget_repo.create_budget.return_value = mock_budget

        # Call service
        budget, error = self.service.create_budget(
            mock_user, 1, date(2024, 1, 1), date(2024, 12, 31), Decimal("1000.00")
        )

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(budget, mock_budget)
        self.mock_budget_repo.create_budget.assert_called_once()

    def test_create_budget_invalid_dates(self):
        """Test creating budget with invalid dates."""
        mock_user = Mock()

        # Call service with invalid dates
        budget, error = self.service.create_budget(
            mock_user, 1, date(2024, 12, 31), date(2024, 1, 1), Decimal("1000.00")
        )

        # Assert error
        self.assertIsNone(budget)
        self.assertIn("before", error)
        self.mock_budget_repo.create_budget.assert_not_called()

    def test_create_budget_category_not_found(self):
        """Test creating budget with invalid category."""
        mock_user = Mock()

        # Mock category not found
        self.mock_category_repo.get_by_id.return_value = None

        # Call service
        budget, error = self.service.create_budget(
            mock_user, 999, date(2024, 1, 1), date(2024, 12, 31), Decimal("1000.00")
        )

        # Assert error
        self.assertIsNone(budget)
        self.assertEqual(error, "Category not found for user")

    def test_create_budget_with_overlap(self):
        """Test creating budget that overlaps existing budget."""
        mock_user = Mock()
        mock_category = Mock()

        # Mock category found
        self.mock_category_repo.get_by_id.return_value = mock_category

        # Mock overlapping budget exists
        mock_existing_budget = Mock()
        mock_existing_budget.start_date = date(2024, 1, 1)
        mock_existing_budget.end_date = date(2024, 6, 30)
        self.mock_budget_repo.get_overlapping_budgets.return_value = [
            mock_existing_budget
        ]

        # Call service (trying to create budget that overlaps)
        budget, error = self.service.create_budget(
            mock_user, 1, date(2024, 3, 1), date(2024, 9, 30), Decimal("1000.00")
        )

        # Assert error
        self.assertIsNone(budget)
        self.assertIn("overlaps", error)
        self.mock_budget_repo.create_budget.assert_not_called()

    def test_get_budget_rankings(self):
        """Test getting budget rankings."""
        mock_user = Mock()

        # Mock budgets
        mock_category1 = Mock()
        mock_category1.name = "Food"
        mock_budget1 = Mock()
        mock_budget1.category = mock_category1
        mock_budget1.amount = Decimal("500.00")

        mock_category2 = Mock()
        mock_category2.name = "Transport"
        mock_budget2 = Mock()
        mock_budget2.category = mock_category2
        mock_budget2.amount = Decimal("300.00")

        self.mock_budget_repo.get_active_budgets_for_date_range.return_value = [
            mock_budget1,
            mock_budget2,
        ]

        # Mock expenses
        self.mock_expense_repo.get_category_expense_sum.side_effect = [
            Decimal("400.00"),  # Food: 80%
            Decimal("270.00"),  # Transport: 90%
        ]

        # Call service
        rankings = self.service.get_budget_rankings(mock_user, 2024, 1)

        # Assert results
        self.assertEqual(len(rankings), 2)
        # Should be sorted by percent (Transport 90% first, Food 80% second)
        self.assertEqual(rankings[0]["name"], "Transport")
        self.assertEqual(rankings[0]["percent"], 90)
        self.assertEqual(rankings[1]["name"], "Food")
        self.assertEqual(rankings[1]["percent"], 80)

    def test_get_budget_progress(self):
        """Test getting budget progress."""
        mock_user = Mock()

        # Mock budget
        mock_category = Mock()
        mock_category.name = "Food"
        mock_budget = Mock()
        mock_budget.category = mock_category
        mock_budget.amount = Decimal("1000.00")

        self.mock_budget_repo.get_active_budgets_for_date_range.return_value = [
            mock_budget
        ]

        # Mock expenses
        self.mock_expense_repo.get_category_expense_sum.return_value = Decimal("600.00")

        # Call service
        result = self.service.get_budget_progress(mock_user, 2024, 1)

        # Assert structure
        self.assertIn("budgets", result)
        self.assertIn("start_date", result)
        self.assertIn("end_date", result)

        # Assert budget data
        budgets = result["budgets"]
        self.assertEqual(len(budgets), 1)
        self.assertEqual(budgets[0]["category"], "Food")
        self.assertEqual(budgets[0]["budget"], 1000.00)
        self.assertEqual(budgets[0]["spent"], 600.00)
        self.assertEqual(budgets[0]["percentage"], 60)
        self.assertEqual(budgets[0]["remaining"], 400.00)

    def test_get_field_choices(self):
        """Test getting field choices."""
        mock_user = Mock()

        # Mock categories
        mock_categories = Mock()
        mock_categories.values.return_value = [
            {"id": 1, "name": "Food"},
            {"id": 2, "name": "Transport"},
        ]
        self.mock_category_repo.get_user_categories.return_value = mock_categories

        # Call service
        result = self.service.get_field_choices(mock_user)

        # Assert structure
        self.assertIn("category", result)
        self.assertEqual(len(result["category"]), 2)
        self.assertEqual(result["category"][0]["value"], 1)
        self.assertEqual(result["category"][0]["label"], "Food")
