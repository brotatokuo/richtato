"""Temporary repository for CardAccount queries needed by Expense."""

from django.db.models import QuerySet
from apps.card.models import CardAccount


class CardAccountRepository:
    """Temporary repository for CardAccount data access needed by Expense."""

    def get_by_id(self, account_id: int, user) -> CardAccount | None:
        """Get a card account by ID with user ownership check."""
        try:
            return CardAccount.objects.get(id=account_id, user=user)
        except CardAccount.DoesNotExist:
            return None

    def get_user_accounts(self, user) -> QuerySet[CardAccount]:
        """Get all card accounts for a user."""
        return CardAccount.objects.filter(user=user).order_by("name")
