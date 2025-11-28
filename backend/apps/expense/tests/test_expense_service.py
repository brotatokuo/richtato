"""Unit tests for ExpenseService - no database access."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock
from django.test import SimpleTestCase

from apps.expense.services import ExpenseService


class ExpenseServiceTestCase(SimpleTestCase):
    """Unit tests for ExpenseService with mocked repositories (NO DB)."""

    def setUp(self):
        """Set up test fixtures with mocked repositories."""
        self.mock_expense_repo = Mock()
        self.mock_account_repo = Mock()
        self.mock_category_repo = Mock()
        self.service = ExpenseService(
            self.mock_expense_repo, self.mock_account_repo, self.mock_category_repo
        )

    def test_get_user_expenses_formatted(self):
        """Test getting formatted user expenses."""
        mock_user = Mock()

        # Mock repository return value
        self.mock_expense_repo.get_user_expenses_annotated.return_value = [
            {
                "id": 1,
                "date": date(2024, 1, 15),
                "description": "Grocery",
                "amount": Decimal("50.00"),
                "Account": "Chase",
                "Category": "Food",
            },
        ]

        # Call service method
        result = self.service.get_user_expenses_formatted(mock_user)

        # Assert repository was called correctly
        self.mock_expense_repo.get_user_expenses_annotated.assert_called_once_with(
            mock_user, None, None
        )

        # Assert result structure
        self.assertIn("columns", result)
        self.assertIn("rows", result)
        self.assertEqual(len(result["rows"]), 1)

    def test_create_expense_success(self):
        """Test creating an expense successfully."""
        mock_user = Mock()
        mock_account = Mock()
        mock_account.id = 1
        mock_category = Mock()
        mock_category.id = 1

        # Mock account and category repositories
        self.mock_account_repo.get_by_id.return_value = mock_account
        self.mock_category_repo.get_by_id.return_value = mock_category

        # Mock expense creation
        mock_expense = Mock()
        mock_expense.id = 1
        self.mock_expense_repo.create_expense.return_value = mock_expense

        # Call service
        expense, error = self.service.create_expense(
            mock_user, 1, "Lunch", date(2024, 1, 15), Decimal("25.00"), 1
        )

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(expense, mock_expense)
        self.mock_expense_repo.create_expense.assert_called_once()

    def test_create_expense_account_not_found(self):
        """Test creating expense with invalid account."""
        mock_user = Mock()

        # Mock account not found
        self.mock_account_repo.get_by_id.return_value = None

        # Call service
        expense, error = self.service.create_expense(
            mock_user, 999, "Lunch", date(2024, 1, 15), Decimal("25.00")
        )

        # Assert error
        self.assertIsNone(expense)
        self.assertEqual(error, "Account not found for user")
        self.mock_expense_repo.create_expense.assert_not_called()

    def test_create_expense_category_not_found(self):
        """Test creating expense with invalid category."""
        mock_user = Mock()
        mock_account = Mock()

        # Mock account found, category not found
        self.mock_account_repo.get_by_id.return_value = mock_account
        self.mock_category_repo.get_by_id.return_value = None

        # Call service
        expense, error = self.service.create_expense(
            mock_user, 1, "Lunch", date(2024, 1, 15), Decimal("25.00"), 999
        )

        # Assert error
        self.assertIsNone(expense)
        self.assertEqual(error, "Category not found for user")

    def test_get_graph_data_by_day(self):
        """Test generating graph data by day."""
        mock_user = Mock()

        # Mock repository returns expense by day
        today = date.today()
        yesterday = today - timedelta(days=1)
        self.mock_expense_repo.get_expenses_grouped_by_day.return_value = {
            yesterday: Decimal("50.00"),
            today: Decimal("75.00"),
        }

        # Call service
        result = self.service.get_graph_data_by_day(mock_user, days=30)

        # Assert result structure
        self.assertIn("labels", result)
        self.assertIn("values", result)
        self.assertEqual(len(result["labels"]), 31)  # 30 days + today
        self.assertEqual(len(result["values"]), 31)

    def test_get_graph_data_by_month(self):
        """Test generating graph data by month."""
        mock_user = Mock()

        # Mock expense entries
        mock_entry1 = Mock()
        mock_entry1.date = date(2024, 1, 15)
        mock_entry2 = Mock()
        mock_entry2.date = date(2024, 2, 10)

        self.mock_expense_repo.get_user_expenses_limited.return_value = [
            mock_entry1,
            mock_entry2,
        ]

        # Mock monthly totals
        self.mock_expense_repo.get_expenses_grouped_by_month.return_value = {
            (2024, 1): Decimal("500.00"),
            (2024, 2): Decimal("600.00"),
        }

        # Call service
        result = self.service.get_graph_data_by_month(mock_user)

        # Assert result structure
        self.assertIn("labels", result)
        self.assertIn("values", result)
        self.assertEqual(len(result["labels"]), 2)
        self.assertEqual(len(result["values"]), 2)

        # Assert labels formatted correctly
        self.assertIn("Jan", result["labels"][0])
        self.assertIn("Feb", result["labels"][1])

    def test_get_field_choices(self):
        """Test getting field choices."""
        mock_user = Mock()

        # Mock repositories
        mock_accounts = Mock()
        mock_accounts.values.return_value = [
            {"id": 1, "name": "Chase"},
            {"id": 2, "name": "Amex"},
        ]
        self.mock_account_repo.get_user_accounts.return_value = mock_accounts

        mock_categories = Mock()
        mock_categories.values.return_value = [
            {"id": 1, "name": "Food"},
            {"id": 2, "name": "Transport"},
        ]
        self.mock_category_repo.get_user_categories.return_value = mock_categories

        # Call service
        result = self.service.get_field_choices(mock_user)

        # Assert structure
        self.assertIn("account", result)
        self.assertIn("category", result)
        self.assertEqual(len(result["account"]), 2)
        self.assertEqual(len(result["category"]), 2)

    def test_get_existing_years(self):
        """Test getting existing years for user."""
        mock_user = Mock()

        # Mock repository
        self.mock_expense_repo.get_existing_years_for_user.return_value = [
            2022,
            2023,
            2024,
        ]

        # Call service
        result = self.service.get_existing_years(mock_user)

        # Assert result
        self.assertEqual(result, [2022, 2023, 2024])
        self.mock_expense_repo.get_existing_years_for_user.assert_called_once_with(
            mock_user
        )
