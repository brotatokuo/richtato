"""Unit tests for AccountService - no database access."""

from datetime import date
from unittest.mock import Mock
from django.test import SimpleTestCase

from apps.account.services import AccountService


class AccountServiceTestCase(SimpleTestCase):
    """Unit tests for AccountService with mocked repositories (NO DB)."""

    def setUp(self):
        """Set up test fixtures with mocked repositories."""
        self.mock_account_repo = Mock()
        self.mock_transaction_repo = Mock()
        self.service = AccountService(
            self.mock_account_repo, self.mock_transaction_repo
        )

    def test_get_user_accounts_formatted(self):
        """Test getting formatted user accounts."""
        # Mock user
        mock_user = Mock()

        # Mock repository return value - dates should be date objects
        self.mock_account_repo.get_user_accounts_annotated.return_value = [
            {
                "id": 1,
                "name": "Checking",
                "type": "checking",
                "entity": "chase",
                "balance": 1000.00,
                "date": date(2024, 1, 1),
            },
            {
                "id": 2,
                "name": "Savings",
                "type": "savings",
                "entity": "bank_of_america",
                "balance": 5000.00,
                "date": date(2024, 1, 2),
            },
        ]

        # Call service method
        result = self.service.get_user_accounts_formatted(mock_user)

        # Assert repository was called correctly
        self.mock_account_repo.get_user_accounts_annotated.assert_called_once_with(
            mock_user
        )

        # Assert result structure
        self.assertIn("columns", result)
        self.assertIn("rows", result)
        self.assertEqual(len(result["rows"]), 2)

        # Assert formatting was applied
        first_row = result["rows"][0]
        self.assertEqual(first_row["type"], "Checking")  # Title case
        self.assertEqual(first_row["entity"], "Chase")  # Title case

    def test_create_account_success(self):
        """Test creating an account successfully."""
        mock_user = Mock()
        account_data = {
            "name": "New Account",
            "type": "checking",
            "asset_entity_name": "chase",
        }

        # Mock repository
        mock_account = Mock()
        mock_account.id = 1
        mock_account.name = "New Account"
        self.mock_account_repo.create_account.return_value = mock_account

        # Call service
        account, error = self.service.create_account(mock_user, account_data)

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(account.id, 1)
        self.mock_account_repo.create_account.assert_called_once_with(
            user=mock_user, **account_data
        )

    def test_create_account_missing_required_field(self):
        """Test creating account with missing required field."""
        mock_user = Mock()
        incomplete_data = {"name": "Incomplete"}  # Missing type and asset_entity_name

        # Call service
        account, error = self.service.create_account(mock_user, incomplete_data)

        # Assert error
        self.assertIsNone(account)
        self.assertIn("Missing required field", error)
        self.mock_account_repo.create_account.assert_not_called()

    def test_update_account_success(self):
        """Test updating an account successfully."""
        mock_user = Mock()
        account_id = 1
        update_data = {"name": "Updated Name"}

        # Mock repository
        mock_account = Mock()
        mock_account.id = account_id
        self.mock_account_repo.get_by_id.return_value = mock_account
        self.mock_account_repo.update_account.return_value = mock_account

        # Call service
        updated, error = self.service.update_account(mock_user, account_id, update_data)

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(updated, mock_account)
        self.mock_account_repo.get_by_id.assert_called_once_with(account_id, mock_user)
        self.mock_account_repo.update_account.assert_called_once()

    def test_update_account_not_found(self):
        """Test updating non-existent account."""
        mock_user = Mock()
        account_id = 999
        update_data = {"name": "Updated Name"}

        # Mock repository - account not found
        self.mock_account_repo.get_by_id.return_value = None

        # Call service
        updated, error = self.service.update_account(mock_user, account_id, update_data)

        # Assert error
        self.assertIsNone(updated)
        self.assertEqual(error, "Account not found")
        self.mock_account_repo.update_account.assert_not_called()

    def test_delete_account_success(self):
        """Test deleting an account successfully."""
        mock_user = Mock()
        account_id = 1

        # Mock repository
        mock_account = Mock()
        self.mock_account_repo.get_by_id.return_value = mock_account

        # Call service
        success, error = self.service.delete_account(mock_user, account_id)

        # Assert success
        self.assertTrue(success)
        self.assertIsNone(error)
        self.mock_account_repo.delete_account.assert_called_once_with(mock_account)

    def test_delete_account_not_found(self):
        """Test deleting non-existent account."""
        mock_user = Mock()
        account_id = 999

        # Mock repository - account not found
        self.mock_account_repo.get_by_id.return_value = None

        # Call service
        success, error = self.service.delete_account(mock_user, account_id)

        # Assert error
        self.assertFalse(success)
        self.assertEqual(error, "Account not found")
        self.mock_account_repo.delete_account.assert_not_called()

    def test_get_field_choices(self):
        """Test getting field choices (static method)."""
        choices = AccountService.get_field_choices()

        # Assert structure
        self.assertIn("type", choices)
        self.assertIn("entity", choices)
        self.assertIsInstance(choices["type"], list)
        self.assertIsInstance(choices["entity"], list)

        # Assert choices have correct format
        if choices["type"]:
            first_choice = choices["type"][0]
            self.assertIn("value", first_choice)
            self.assertIn("label", first_choice)
