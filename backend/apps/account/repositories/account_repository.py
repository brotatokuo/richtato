"""Repository for managing Account data access."""

from django.db.models import F, QuerySet
from apps.account.models import Account


class AccountRepository:
    """Repository for managing Account data access - ORM layer only."""

    def get_by_id(self, account_id: int, user) -> Account | None:
        """Get an account by ID with user ownership check."""
        try:
            return Account.objects.get(id=account_id, user=user)
        except Account.DoesNotExist:
            return None

    def get_user_accounts(self, user) -> QuerySet[Account]:
        """Get all accounts for user with optimized query."""
        return Account.objects.filter(user=user).order_by("name")

    def get_user_accounts_annotated(self, user) -> QuerySet:
        """
        Get user accounts with annotated fields for API responses.

        Annotates:
            - entity: from asset_entity_name
            - balance: from latest_balance
            - date: from latest_balance_date
        """
        return (
            Account.objects.filter(user=user)
            .annotate(
                entity=F("asset_entity_name"),
                balance=F("latest_balance"),
                date=F("latest_balance_date"),
            )
            .order_by("name")
            .values("id", "name", "type", "entity", "balance", "date")
        )

    def get_user_accounts_for_choices(self, user) -> QuerySet:
        """Get user accounts as id/name pairs for dropdown choices."""
        return Account.objects.filter(user=user).values("id", "name")

    def create_account(self, user, **account_data) -> Account:
        """Create a new account."""
        return Account.objects.create(user=user, **account_data)

    def update_account(self, account: Account, **data) -> Account:
        """Update account fields."""
        for key, value in data.items():
            setattr(account, key, value)
        account.save()
        return account

    def delete_account(self, account: Account) -> None:
        """Delete an account."""
        account.delete()

    def update_latest_balance(self, account: Account, amount, date) -> None:
        """Update the latest balance and date for an account."""
        account.latest_balance = amount
        account.latest_balance_date = date
        account.save()
