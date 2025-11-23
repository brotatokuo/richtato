"""Service layer for CardAccount operations."""

from apps.richtato_user.repositories.card_account_repository import (
    CardAccountRepository,
)
from apps.richtato_user.models import supported_card_banks


class CardAccountService:
    """Service for CardAccount business logic."""

    def __init__(
        self,
        card_account_repo: CardAccountRepository | None = None,
    ):
        self.card_account_repo = card_account_repo or CardAccountRepository()

    def get_user_card_accounts_formatted(self, user) -> list[dict]:
        """Get all card accounts for a user formatted for API response."""
        card_accounts = self.card_account_repo.get_user_card_accounts(user)
        return [{"id": c.id, "name": c.name, "bank": c.bank} for c in card_accounts]

    def get_card_account_by_id(self, card_account_id: int, user) -> dict | None:
        """Get a single card account by ID."""
        card = self.card_account_repo.get_by_id(card_account_id, user)
        if card:
            return {"id": card.id, "name": card.name, "bank": card.bank}
        return None

    def create_card_account(self, user, name: str, bank: str) -> dict:
        """Create a new card account."""
        card = self.card_account_repo.create_card_account(user, name, bank)
        return {"id": card.id, "name": card.name, "bank": card.bank}

    def update_card_account(self, card_account_id: int, user, **data) -> dict:
        """Update a card account."""
        card = self.card_account_repo.get_by_id(card_account_id, user)
        if not card:
            raise ValueError("Card account not found")

        updated_card = self.card_account_repo.update_card_account(card, **data)
        return {
            "id": updated_card.id,
            "name": updated_card.name,
            "bank": updated_card.bank,
        }

    def delete_card_account(self, card_account_id: int, user) -> None:
        """Delete a card account."""
        card = self.card_account_repo.get_by_id(card_account_id, user)
        if not card:
            raise ValueError("Card account not found")
        self.card_account_repo.delete_card_account(card)

    def get_field_choices(self) -> dict:
        """Get field choices for CardAccount model."""
        return {
            "bank": [
                {"value": value, "label": label}
                for value, label in supported_card_banks
            ]
        }
