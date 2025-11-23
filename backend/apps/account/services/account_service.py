"""Service layer for Account business logic."""

from apps.account.models import account_types, supported_asset_accounts
from utilities.tools import format_currency, format_date


class AccountService:
    """Service for managing Account business logic - no ORM calls."""

    def __init__(self, account_repo, transaction_repo):
        """
        Initialize service with repository dependencies.

        Args:
            account_repo: AccountRepository instance
            transaction_repo: AccountTransactionRepository instance
        """
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo

    def get_user_accounts_formatted(self, user) -> dict:
        """
        Get user accounts with formatted data for API response.

        Business logic: Formats currency and dates for display.

        Args:
            user: User instance

        Returns:
            Dictionary with columns and rows for table display
        """
        accounts = self.account_repo.get_user_accounts_annotated(user)

        rows = []
        for account in accounts:
            rows.append(
                {
                    **account,
                    "type": account["type"].title(),
                    "entity": account["entity"].title(),
                    "balance": format_currency(account["balance"]),
                    "date": format_date(account["date"]) if account["date"] else None,
                }
            )

        return {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "name", "title": "Name"},
                {"field": "type", "title": "Type"},
                {"field": "entity", "title": "Entity"},
                {"field": "balance", "title": "Balance"},
            ],
            "rows": rows,
        }

    def create_account(self, user, account_data: dict) -> tuple[object, str | None]:
        """
        Create a new account with validation.

        Business logic: Validates account data before creation.

        Args:
            user: User instance
            account_data: Dictionary of account fields

        Returns:
            Tuple of (account instance, error message or None)
        """
        # Business rule: Validate required fields
        required_fields = ["name", "type", "asset_entity_name"]
        for field in required_fields:
            if field not in account_data:
                return None, f"Missing required field: {field}"

        # Create account via repository
        account = self.account_repo.create_account(user=user, **account_data)
        return account, None

    def update_account(
        self, user, account_id: int, data: dict
    ) -> tuple[object | None, str | None]:
        """
        Update an existing account with validation.

        Business logic: Validates ownership and updates only allowed fields.

        Args:
            user: User instance
            account_id: Account ID to update
            data: Dictionary of fields to update

        Returns:
            Tuple of (updated account or None, error message or None)
        """
        # Business rule: Check ownership
        account = self.account_repo.get_by_id(account_id, user)
        if not account:
            return None, "Account not found"

        # Business rule: Only allow updating specific fields
        allowed_fields = ["name", "type", "asset_entity_name"]
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}

        # Update via repository
        updated_account = self.account_repo.update_account(account, **filtered_data)
        return updated_account, None

    def delete_account(self, user, account_id: int) -> tuple[bool, str | None]:
        """
        Delete an account with ownership validation.

        Business logic: Validates ownership before deletion.

        Args:
            user: User instance
            account_id: Account ID to delete

        Returns:
            Tuple of (success boolean, error message or None)
        """
        # Business rule: Check ownership
        account = self.account_repo.get_by_id(account_id, user)
        if not account:
            return False, "Account not found"

        # Delete via repository
        self.account_repo.delete_account(account)
        return True, None

    @staticmethod
    def get_field_choices() -> dict:
        """
        Get field choices for account types and entities.

        Business logic: Formats static choices for API consumption.

        Returns:
            Dictionary with type and entity choices
        """
        return {
            "type": [
                {"value": value, "label": label} for value, label in account_types
            ],
            "entity": [
                {"value": value, "label": label}
                for value, label in supported_asset_accounts
            ],
        }
