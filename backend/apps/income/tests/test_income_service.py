"""Unit tests for IncomeService - no database access."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock
from django.test import SimpleTestCase

from apps.income.services import IncomeService


class IncomeServiceTestCase(SimpleTestCase):
    """Unit tests for IncomeService with mocked repositories (NO DB)."""

    def setUp(self):
        """Set up test fixtures with mocked repositories."""
        self.mock_income_repo = Mock()
        self.mock_account_repo = Mock()
        self.service = IncomeService(self.mock_income_repo, self.mock_account_repo)

    def test_get_user_income_formatted(self):
        """Test getting formatted user income entries."""
        mock_user = Mock()

        # Mock repository return value
        self.mock_income_repo.get_user_income_annotated.return_value = [
            {
                "id": 1,
                "date": date(2024, 1, 15),
                "Account": "Checking",
                "description": "Salary",
                "amount": Decimal("5000.00"),
            },
            {
                "id": 2,
                "date": date(2024, 1, 10),
                "Account": "Savings",
                "description": "Bonus",
                "amount": Decimal("1000.00"),
            },
        ]

        # Call service method
        result = self.service.get_user_income_formatted(mock_user)

        # Assert repository was called correctly
        self.mock_income_repo.get_user_income_annotated.assert_called_once_with(
            mock_user, None, None
        )

        # Assert result structure
        self.assertIn("columns", result)
        self.assertIn("rows", result)
        self.assertEqual(len(result["rows"]), 2)

    def test_get_user_income_formatted_with_limit(self):
        """Test getting formatted income with limit."""
        mock_user = Mock()

        # Mock repository return value
        mock_queryset = [
            {
                "id": 1,
                "date": date(2024, 1, 15),
                "Account": "Checking",
                "description": "Salary",
                "amount": Decimal("5000.00"),
            },
            {
                "id": 2,
                "date": date(2024, 1, 10),
                "Account": "Savings",
                "description": "Bonus",
                "amount": Decimal("1000.00"),
            },
            {
                "id": 3,
                "date": date(2024, 1, 5),
                "Account": "Checking",
                "description": "Freelance",
                "amount": Decimal("500.00"),
            },
        ]
        self.mock_income_repo.get_user_income_annotated.return_value = mock_queryset

        # Call service with limit
        result = self.service.get_user_income_formatted(mock_user, limit=2)

        # Assert only 2 rows returned
        self.assertEqual(len(result["rows"]), 2)

    def test_create_income_success(self):
        """Test creating an income entry successfully."""
        mock_user = Mock()
        mock_account = Mock()
        mock_account.id = 1

        # Mock account repository
        self.mock_account_repo.get_by_id.return_value = mock_account

        # Mock income creation
        mock_income = Mock()
        mock_income.id = 1
        self.mock_income_repo.create_income.return_value = mock_income

        # Call service
        income, error = self.service.create_income(
            mock_user, 1, "Salary", date(2024, 1, 15), Decimal("5000.00")
        )

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(income, mock_income)
        self.mock_account_repo.get_by_id.assert_called_once_with(1, mock_user)
        self.mock_income_repo.create_income.assert_called_once()

    def test_create_income_account_not_found(self):
        """Test creating income with invalid account."""
        mock_user = Mock()

        # Mock account not found
        self.mock_account_repo.get_by_id.return_value = None

        # Call service
        income, error = self.service.create_income(
            mock_user, 999, "Salary", date(2024, 1, 15), Decimal("5000.00")
        )

        # Assert error
        self.assertIsNone(income)
        self.assertEqual(error, "Account not found for user")
        self.mock_income_repo.create_income.assert_not_called()

    def test_update_income_success(self):
        """Test updating an income entry successfully."""
        mock_user = Mock()
        income_id = 1
        update_data = {"description": "Updated Salary"}

        # Mock income repository
        mock_income = Mock()
        mock_income.id = income_id
        self.mock_income_repo.get_by_id.return_value = mock_income
        self.mock_income_repo.update_income.return_value = mock_income

        # Call service
        updated, error = self.service.update_income(mock_user, income_id, update_data)

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(updated, mock_income)
        self.mock_income_repo.get_by_id.assert_called_once_with(income_id, mock_user)
        self.mock_income_repo.update_income.assert_called_once()

    def test_update_income_not_found(self):
        """Test updating non-existent income."""
        mock_user = Mock()
        income_id = 999
        update_data = {"description": "Updated"}

        # Mock income not found
        self.mock_income_repo.get_by_id.return_value = None

        # Call service
        updated, error = self.service.update_income(mock_user, income_id, update_data)

        # Assert error
        self.assertIsNone(updated)
        self.assertEqual(error, "Income not found")
        self.mock_income_repo.update_income.assert_not_called()

    def test_update_income_with_account_validation(self):
        """Test updating income with account field validates ownership."""
        mock_user = Mock()
        income_id = 1
        update_data = {"account_name": 2}

        # Mock income
        mock_income = Mock()
        self.mock_income_repo.get_by_id.return_value = mock_income

        # Mock account not found
        self.mock_account_repo.get_by_id.return_value = None

        # Call service
        updated, error = self.service.update_income(mock_user, income_id, update_data)

        # Assert error
        self.assertIsNone(updated)
        self.assertEqual(error, "Account not found for user")

    def test_delete_income_success(self):
        """Test deleting an income entry successfully."""
        mock_user = Mock()
        income_id = 1

        # Mock income
        mock_income = Mock()
        self.mock_income_repo.get_by_id.return_value = mock_income

        # Call service
        success, error = self.service.delete_income(mock_user, income_id)

        # Assert success
        self.assertTrue(success)
        self.assertIsNone(error)
        self.mock_income_repo.delete_income.assert_called_once_with(mock_income)

    def test_delete_income_not_found(self):
        """Test deleting non-existent income."""
        mock_user = Mock()
        income_id = 999

        # Mock income not found
        self.mock_income_repo.get_by_id.return_value = None

        # Call service
        success, error = self.service.delete_income(mock_user, income_id)

        # Assert error
        self.assertFalse(success)
        self.assertEqual(error, "Income not found")
        self.mock_income_repo.delete_income.assert_not_called()

    def test_get_graph_data_by_day(self):
        """Test generating graph data by day."""
        mock_user = Mock()

        # Mock repository returns income by day
        today = date.today()
        yesterday = today - timedelta(days=1)
        self.mock_income_repo.get_income_grouped_by_day.return_value = {
            yesterday: Decimal("100.00"),
            today: Decimal("200.00"),
        }

        # Call service
        result = self.service.get_graph_data_by_day(mock_user, days=30)

        # Assert result structure
        self.assertIn("labels", result)
        self.assertIn("values", result)
        self.assertEqual(len(result["labels"]), 31)  # 30 days + today
        self.assertEqual(len(result["values"]), 31)

        # Assert repository was called
        self.mock_income_repo.get_income_grouped_by_day.assert_called_once()

    def test_get_graph_data_by_month(self):
        """Test generating graph data by month."""
        mock_user = Mock()

        # Mock income entries
        mock_entry1 = Mock()
        mock_entry1.date = date(2024, 1, 15)
        mock_entry2 = Mock()
        mock_entry2.date = date(2024, 2, 10)

        self.mock_income_repo.get_user_income_limited.return_value = [
            mock_entry1,
            mock_entry2,
        ]

        # Mock monthly totals
        self.mock_income_repo.get_income_grouped_by_month.return_value = {
            (2024, 1): Decimal("5000.00"),
            (2024, 2): Decimal("6000.00"),
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

    def test_get_graph_data_by_month_no_data(self):
        """Test graph data by month with no income entries."""
        mock_user = Mock()

        # Mock empty income
        self.mock_income_repo.get_user_income_limited.return_value = []

        # Call service
        result = self.service.get_graph_data_by_month(mock_user)

        # Assert empty result
        self.assertEqual(result["labels"], [])
        self.assertEqual(result["values"], [])

    def test_get_field_choices(self):
        """Test getting field choices for income creation."""
        mock_user = Mock()

        # Mock account repository
        mock_accounts = Mock()
        mock_accounts.values.return_value = [
            {"id": 1, "name": "Checking"},
            {"id": 2, "name": "Savings"},
        ]
        self.mock_account_repo.get_user_accounts.return_value = mock_accounts

        # Call service
        result = self.service.get_field_choices(mock_user)

        # Assert structure
        self.assertIn("account", result)
        self.assertEqual(len(result["account"]), 2)

        # Assert format
        first_choice = result["account"][0]
        self.assertIn("value", first_choice)
        self.assertIn("label", first_choice)
