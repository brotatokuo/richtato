"""Unit tests for AccountTransactionService - no database access."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from django.test import SimpleTestCase

from apps.account.services import AccountTransactionService


class AccountTransactionServiceTestCase(SimpleTestCase):
    """Unit tests for AccountTransactionService with mocked repositories (NO DB)."""

    def setUp(self):
        """Set up test fixtures with mocked repositories."""
        self.mock_account_repo = Mock()
        self.mock_transaction_repo = Mock()
        self.service = AccountTransactionService(
            self.mock_account_repo, self.mock_transaction_repo
        )

    def test_create_transaction_updates_balance_when_latest(self):
        """Test that creating a transaction updates account balance when it's the latest."""
        # Mock account with older balance date
        mock_account = Mock()
        mock_account.latest_balance_date = date(2024, 1, 1)

        # Mock transaction
        mock_transaction = Mock()
        mock_transaction.id = 1
        mock_transaction.amount = Decimal("500.00")
        mock_transaction.date = date(2024, 1, 15)
        self.mock_transaction_repo.create_transaction.return_value = mock_transaction

        # Call service
        transaction, error = self.service.create_transaction(
            mock_account, Decimal("500.00"), date(2024, 1, 15)
        )

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(transaction, mock_transaction)

        # Assert balance was updated (transaction date is later)
        self.mock_account_repo.update_latest_balance.assert_called_once_with(
            mock_account, Decimal("500.00"), date(2024, 1, 15)
        )

    def test_create_transaction_does_not_update_balance_when_older(self):
        """Test that creating an older transaction doesn't update account balance."""
        # Mock account with newer balance date
        mock_account = Mock()
        mock_account.latest_balance_date = date(2024, 1, 15)

        # Mock transaction
        mock_transaction = Mock()
        mock_transaction.id = 1
        mock_transaction.amount = Decimal("500.00")
        mock_transaction.date = date(2024, 1, 1)
        self.mock_transaction_repo.create_transaction.return_value = mock_transaction

        # Call service
        transaction, error = self.service.create_transaction(
            mock_account, Decimal("500.00"), date(2024, 1, 1)
        )

        # Assert success
        self.assertIsNone(error)

        # Assert balance was NOT updated (transaction date is older)
        self.mock_account_repo.update_latest_balance.assert_not_called()

    def test_create_transaction_with_no_previous_balance(self):
        """Test creating first transaction updates balance."""
        # Mock account with no balance date
        mock_account = Mock()
        mock_account.latest_balance_date = None

        # Mock transaction
        mock_transaction = Mock()
        self.mock_transaction_repo.create_transaction.return_value = mock_transaction

        # Call service
        transaction, error = self.service.create_transaction(
            mock_account, Decimal("1000.00"), date(2024, 1, 1)
        )

        # Assert success and balance updated
        self.assertIsNone(error)
        self.mock_account_repo.update_latest_balance.assert_called_once()

    def test_update_transaction_success(self):
        """Test updating a transaction successfully."""
        mock_account = Mock()
        transaction_id = 1
        update_data = {"amount": Decimal("750.00")}

        # Mock transaction
        mock_transaction = Mock()
        mock_transaction.id = transaction_id
        self.mock_transaction_repo.get_by_id.return_value = mock_transaction
        self.mock_transaction_repo.update_transaction.return_value = mock_transaction

        # Call service
        updated, error = self.service.update_transaction(
            mock_account, transaction_id, update_data
        )

        # Assert success
        self.assertIsNone(error)
        self.assertEqual(updated, mock_transaction)
        self.mock_transaction_repo.update_transaction.assert_called_once()

    def test_update_transaction_not_found(self):
        """Test updating non-existent transaction."""
        mock_account = Mock()
        transaction_id = 999
        update_data = {"amount": Decimal("750.00")}

        # Mock repository - transaction not found
        self.mock_transaction_repo.get_by_id.return_value = None

        # Call service
        updated, error = self.service.update_transaction(
            mock_account, transaction_id, update_data
        )

        # Assert error
        self.assertIsNone(updated)
        self.assertEqual(error, "Transaction not found")
        self.mock_transaction_repo.update_transaction.assert_not_called()

    def test_update_transaction_no_fields(self):
        """Test updating transaction with no updatable fields."""
        mock_account = Mock()
        transaction_id = 1
        update_data = {"invalid_field": "value"}

        # Mock transaction
        mock_transaction = Mock()
        self.mock_transaction_repo.get_by_id.return_value = mock_transaction

        # Call service
        updated, error = self.service.update_transaction(
            mock_account, transaction_id, update_data
        )

        # Assert error
        self.assertIsNone(updated)
        self.assertEqual(error, "No updatable fields provided")

    def test_delete_transaction_and_recompute_balance(self):
        """Test deleting transaction and recalculating balance."""
        mock_account = Mock()
        transaction_id = 1

        # Mock transaction to delete
        mock_transaction = Mock()
        self.mock_transaction_repo.get_by_id.return_value = mock_transaction

        # Mock latest transaction after deletion
        mock_latest = Mock()
        mock_latest.amount = Decimal("1000.00")
        mock_latest.date = date(2024, 1, 10)
        self.mock_transaction_repo.get_latest_transaction.return_value = mock_latest

        # Call service
        success, error = self.service.delete_transaction_and_recompute_balance(
            mock_account, transaction_id
        )

        # Assert success
        self.assertTrue(success)
        self.assertIsNone(error)
        self.mock_transaction_repo.delete_transaction.assert_called_once_with(
            mock_transaction
        )
        # Assert balance was recalculated
        self.mock_account_repo.update_latest_balance.assert_called_once_with(
            mock_account, Decimal("1000.00"), date(2024, 1, 10)
        )

    def test_delete_last_transaction_resets_balance(self):
        """Test deleting last transaction resets balance to zero."""
        mock_account = Mock()
        transaction_id = 1

        # Mock transaction to delete
        mock_transaction = Mock()
        self.mock_transaction_repo.get_by_id.return_value = mock_transaction

        # Mock no remaining transactions
        self.mock_transaction_repo.get_latest_transaction.return_value = None

        # Call service
        success, error = self.service.delete_transaction_and_recompute_balance(
            mock_account, transaction_id
        )

        # Assert success
        self.assertTrue(success)
        self.assertIsNone(error)
        # Assert balance was reset to 0
        self.mock_account_repo.update_latest_balance.assert_called_once_with(
            mock_account, Decimal("0"), None
        )

    def test_get_paginated_transactions(self):
        """Test getting paginated transactions."""
        mock_account = Mock()

        # Mock transactions
        mock_tx1 = Mock()
        mock_tx1.id = 1
        mock_tx1.date = date(2024, 1, 15)
        mock_tx1.amount = Decimal("100.00")

        mock_tx2 = Mock()
        mock_tx2.id = 2
        mock_tx2.date = date(2024, 1, 14)
        mock_tx2.amount = Decimal("200.00")

        self.mock_transaction_repo.get_account_transactions_paginated.return_value = [
            mock_tx1,
            mock_tx2,
        ]
        self.mock_transaction_repo.count_transactions.return_value = 10

        # Call service
        result = self.service.get_paginated_transactions(
            mock_account, page=1, page_size=2
        )

        # Assert result structure
        self.assertIn("columns", result)
        self.assertIn("rows", result)
        self.assertIn("page", result)
        self.assertIn("page_size", result)
        self.assertIn("total", result)

        # Assert pagination metadata
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 2)
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(result["rows"]), 2)

    def test_get_paginated_transactions_validates_parameters(self):
        """Test that pagination parameters are validated."""
        mock_account = Mock()
        self.mock_transaction_repo.get_account_transactions_paginated.return_value = []
        self.mock_transaction_repo.count_transactions.return_value = 0

        # Call with invalid parameters
        result = self.service.get_paginated_transactions(
            mock_account, page=-5, page_size=1000
        )

        # Assert parameters were normalized
        self.assertEqual(result["page"], 1)  # Negative page normalized to 1
        self.assertEqual(result["page_size"], 100)  # Over 100 capped to 100

    def test_get_user_transactions_formatted(self):
        """Test getting formatted user transactions."""
        mock_user = Mock()

        # Mock transactions
        mock_account = Mock()
        mock_account.name = "Checking"

        mock_tx = Mock()
        mock_tx.id = 1
        mock_tx.date = date(2024, 1, 15)
        mock_tx.amount = Decimal("100.00")
        mock_tx.account = mock_account

        self.mock_transaction_repo.get_user_transactions_limited.return_value = [
            mock_tx
        ]

        # Call service
        result = self.service.get_user_transactions_formatted(mock_user, limit=10)

        # Assert result structure
        self.assertIn("columns", result)
        self.assertIn("rows", result)
        self.assertEqual(len(result["rows"]), 1)

        # Assert account name is included
        self.assertEqual(result["rows"][0]["account"], "Checking")
