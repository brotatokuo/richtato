"""Repository for CardAccount data access."""

from django.db.models import QuerySet
from apps.richtato_user.models import CardAccount


class CardAccountRepository:
    """Repository for CardAccount data access - ORM layer only."""

    def get_by_id(self, card_account_id: int, user) -> CardAccount | None:
        """Get a card account by ID with user ownership check."""
        try:
            return CardAccount.objects.get(id=card_account_id, user=user)
        except CardAccount.DoesNotExist:
            return None

    def get_user_card_accounts(self, user) -> QuerySet[CardAccount]:
        """Get all card accounts for a user."""
        return CardAccount.objects.filter(user=user).order_by("name")

    def create_card_account(self, user, name: str, bank: str) -> CardAccount:
        """Create a new card account."""
        return CardAccount.objects.create(user=user, name=name, bank=bank)

    def update_card_account(self, card_account: CardAccount, **data) -> CardAccount:
        """Update card account fields."""
        for key, value in data.items():
            setattr(card_account, key, value)
        card_account.save()
        return card_account

    def delete_card_account(self, card_account: CardAccount) -> None:
        """Delete a card account."""
        card_account.delete()
