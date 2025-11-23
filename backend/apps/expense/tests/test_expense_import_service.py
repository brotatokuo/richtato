"""Unit tests for ExpenseImportService - no database access."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
import pandas as pd
from django.test import SimpleTestCase

from apps.expense.services import ExpenseImportService


class ExpenseImportServiceTestCase(SimpleTestCase):
    """Unit tests for ExpenseImportService with mocked repositories (NO DB)."""

    def setUp(self):
        """Set up test fixtures with mocked repositories."""
        self.mock_expense_repo = Mock()
        self.mock_account_repo = Mock()
        self.mock_category_repo = Mock()
        self.service = ExpenseImportService(
            self.mock_expense_repo, self.mock_account_repo, self.mock_category_repo
        )

    def test_import_from_dataframe_success(self):
        """Test importing expenses from dataframe successfully."""
        mock_user = Mock()

        # Create test dataframe
        df = pd.DataFrame(
            {
                "Card": ["Chase", "Amex"],
                "Category": ["Food", "Transport"],
                "Amount": [Decimal("50.00"), Decimal("30.00")],
                "Date": [date(2024, 1, 15), date(2024, 1, 16)],
                "Description": ["Grocery", "Uber"],
            }
        )

        # Mock account repository
        mock_account1 = Mock()
        mock_account1.name = "Chase"
        mock_account2 = Mock()
        mock_account2.name = "Amex"

        mock_accounts = [mock_account1, mock_account2]
        self.mock_account_repo.get_user_accounts.return_value = mock_accounts

        # Mock category repository
        mock_category1 = Mock()
        mock_category1.name = "Food"
        mock_category2 = Mock()
        mock_category2.name = "Transport"

        mock_categories = [mock_category1, mock_category2]
        self.mock_category_repo.get_user_categories.return_value = mock_categories

        # Call service
        success_count, error_count, errors = self.service.import_from_dataframe(
            df, mock_user
        )

        # Assert results
        self.assertEqual(success_count, 2)
        self.assertEqual(error_count, 0)
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.mock_expense_repo.create_expense.call_count, 2)

    def test_import_from_dataframe_account_not_found(self):
        """Test importing with account not found."""
        mock_user = Mock()

        # Create test dataframe with invalid account
        df = pd.DataFrame(
            {
                "Card": ["InvalidCard"],
                "Category": ["Food"],
                "Amount": [Decimal("50.00")],
                "Date": [date(2024, 1, 15)],
                "Description": ["Grocery"],
            }
        )

        # Mock account repository returns empty list
        self.mock_account_repo.get_user_accounts.return_value = []

        # Call service
        success_count, error_count, errors = self.service.import_from_dataframe(
            df, mock_user
        )

        # Assert results
        self.assertEqual(success_count, 0)
        self.assertEqual(error_count, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("Account", errors[0])
        self.mock_expense_repo.create_expense.assert_not_called()

    def test_categorize_transaction_success(self):
        """Test categorizing transaction with AI successfully."""
        mock_user = Mock()
        mock_ai_service = Mock()

        # Mock AI returns category name
        mock_ai_service.categorize_transaction.return_value = "Food"

        # Mock category repository
        mock_category = Mock()
        mock_category.name = "Food"
        mock_category.id = 1
        self.mock_category_repo.get_user_categories.return_value = [mock_category]

        # Call service
        category_id, error = self.service.categorize_transaction(
            mock_user, "Grocery store", mock_ai_service
        )

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(category_id, 1)

    def test_categorize_transaction_ai_failure_fallback(self):
        """Test categorizing transaction falls back to Unknown when AI fails."""
        mock_user = Mock()
        mock_ai_service = Mock()

        # Mock AI raises exception
        mock_ai_service.categorize_transaction.side_effect = Exception("AI failed")

        # Mock category repository with Unknown
        mock_unknown = Mock()
        mock_unknown.name = "Unknown"
        mock_unknown.id = 99
        self.mock_category_repo.get_user_categories.return_value = [mock_unknown]

        # Call service
        category_id, error = self.service.categorize_transaction(
            mock_user, "Some description", mock_ai_service
        )

        # Assert fallback to Unknown
        self.assertIsNone(error)
        self.assertEqual(category_id, 99)

    def test_categorize_transaction_case_insensitive(self):
        """Test categorizing transaction with case-insensitive match."""
        mock_user = Mock()
        mock_ai_service = Mock()

        # Mock AI returns lowercase
        mock_ai_service.categorize_transaction.return_value = "food"

        # Mock category repository with title case
        mock_category = Mock()
        mock_category.name = "Food"
        mock_category.id = 1
        self.mock_category_repo.get_user_categories.return_value = [mock_category]

        # Call service
        category_id, error = self.service.categorize_transaction(
            mock_user, "Grocery store", mock_ai_service
        )

        # Assert success with case-insensitive match
        self.assertIsNone(error)
        self.assertEqual(category_id, 1)

    def test_categorize_transaction_no_category_found(self):
        """Test categorizing when no suitable category exists."""
        mock_user = Mock()
        mock_ai_service = Mock()

        # Mock AI returns category name
        mock_ai_service.categorize_transaction.return_value = "SomeCategory"

        # Mock category repository returns empty list
        self.mock_category_repo.get_user_categories.return_value = []

        # Call service
        category_id, error = self.service.categorize_transaction(
            mock_user, "Some description", mock_ai_service
        )

        # Assert error
        self.assertIsNone(category_id)
        self.assertIn("No suitable category found", error)
