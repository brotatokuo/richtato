"""Unit tests for CardAccountService."""

from unittest.mock import MagicMock
from django.test import SimpleTestCase
from apps.richtato_user.services.card_account_service import CardAccountService


class TestCardAccountService(SimpleTestCase):
    """Test CardAccountService business logic."""

    def setUp(self):
        self.mock_card_account_repo = MagicMock()
        self.service = CardAccountService(card_account_repo=self.mock_card_account_repo)
        self.mock_user = MagicMock()

    def test_get_user_card_accounts_formatted(self):
        """Test getting formatted card accounts for a user."""
        mock_card1 = MagicMock()
        mock_card1.id = 1
        mock_card1.name = "Chase Sapphire"
        mock_card1.bank = "chase"

        mock_card2 = MagicMock()
        mock_card2.id = 2
        mock_card2.name = "Amex Gold"
        mock_card2.bank = "american_express"

        self.mock_card_account_repo.get_user_card_accounts.return_value = [
            mock_card1,
            mock_card2,
        ]

        result = self.service.get_user_card_accounts_formatted(self.mock_user)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], {"id": 1, "name": "Chase Sapphire", "bank": "chase"}
        )
        self.assertEqual(
            result[1], {"id": 2, "name": "Amex Gold", "bank": "american_express"}
        )

    def test_get_card_account_by_id_found(self):
        """Test getting a card account by ID when it exists."""
        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "Chase Sapphire"
        mock_card.bank = "chase"
        self.mock_card_account_repo.get_by_id.return_value = mock_card

        result = self.service.get_card_account_by_id(1, self.mock_user)

        self.assertEqual(result, {"id": 1, "name": "Chase Sapphire", "bank": "chase"})
        self.mock_card_account_repo.get_by_id.assert_called_once_with(1, self.mock_user)

    def test_get_card_account_by_id_not_found(self):
        """Test getting a card account by ID when it doesn't exist."""
        self.mock_card_account_repo.get_by_id.return_value = None

        result = self.service.get_card_account_by_id(999, self.mock_user)

        self.assertIsNone(result)

    def test_create_card_account(self):
        """Test creating a new card account."""
        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "New Card"
        mock_card.bank = "chase"
        self.mock_card_account_repo.create_card_account.return_value = mock_card

        result = self.service.create_card_account(self.mock_user, "New Card", "chase")

        self.assertEqual(result, {"id": 1, "name": "New Card", "bank": "chase"})
        self.mock_card_account_repo.create_card_account.assert_called_once_with(
            self.mock_user, "New Card", "chase"
        )

    def test_update_card_account_success(self):
        """Test updating a card account successfully."""
        mock_card = MagicMock()
        updated_card = MagicMock()
        updated_card.id = 1
        updated_card.name = "Updated Card"
        updated_card.bank = "chase"

        self.mock_card_account_repo.get_by_id.return_value = mock_card
        self.mock_card_account_repo.update_card_account.return_value = updated_card

        result = self.service.update_card_account(
            1, self.mock_user, name="Updated Card"
        )

        self.assertEqual(result, {"id": 1, "name": "Updated Card", "bank": "chase"})
        self.mock_card_account_repo.update_card_account.assert_called_once_with(
            mock_card, name="Updated Card"
        )

    def test_update_card_account_not_found(self):
        """Test updating a card account that doesn't exist."""
        self.mock_card_account_repo.get_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.update_card_account(999, self.mock_user, name="Updated Card")

        self.assertEqual(str(context.exception), "Card account not found")

    def test_delete_card_account_success(self):
        """Test deleting a card account successfully."""
        mock_card = MagicMock()
        self.mock_card_account_repo.get_by_id.return_value = mock_card

        self.service.delete_card_account(1, self.mock_user)

        self.mock_card_account_repo.delete_card_account.assert_called_once_with(
            mock_card
        )

    def test_delete_card_account_not_found(self):
        """Test deleting a card account that doesn't exist."""
        self.mock_card_account_repo.get_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.delete_card_account(999, self.mock_user)

        self.assertEqual(str(context.exception), "Card account not found")

    def test_get_field_choices(self):
        """Test getting field choices for CardAccount."""
        result = self.service.get_field_choices()

        self.assertIn("bank", result)
        self.assertTrue(len(result["bank"]) > 0)
        self.assertIn("value", result["bank"][0])
        self.assertIn("label", result["bank"][0])
