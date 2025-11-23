"""Service layer for AccountTransaction business logic."""

from datetime import datetime
from decimal import Decimal

from utilities.tools import format_currency, format_date


class AccountTransactionService:
    """Service for managing AccountTransaction business logic - no ORM calls."""

    def __init__(self, account_repo, transaction_repo):
        """
        Initialize service with repository dependencies.

        Args:
            account_repo: AccountRepository instance
            transaction_repo: AccountTransactionRepository instance
        """
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo

    def create_transaction(self, account, amount, date) -> tuple[object, str | None]:
        """
        Create a new transaction and update account balance if needed.

        Business logic: Determines if this transaction should update the account's
        latest balance based on the transaction date.

        Args:
            account: Account instance
            amount: Transaction amount
            date: Transaction date

        Returns:
            Tuple of (transaction instance, error message or None)
        """
        # Parse date if string
        if isinstance(date, str):
            transaction_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            transaction_date = date

        # Create transaction first
        transaction = self.transaction_repo.create_transaction(
            account, amount, transaction_date
        )

        # Business rule: Update account balance if this is the latest transaction
        latest_balance_date = account.latest_balance_date
        if isinstance(latest_balance_date, str):
            latest_balance_date = datetime.strptime(
                latest_balance_date, "%Y-%m-%d"
            ).date()

        if latest_balance_date is None or transaction_date >= latest_balance_date:
            self.account_repo.update_latest_balance(account, amount, transaction_date)

        return transaction, None

    def update_transaction(
        self, account, transaction_id: int, data: dict
    ) -> tuple[object | None, str | None]:
        """
        Update an existing transaction.

        Business logic: Validates transaction exists and updates allowed fields.

        Args:
            account: Account instance
            transaction_id: Transaction ID to update
            data: Dictionary of fields to update

        Returns:
            Tuple of (updated transaction or None, error message or None)
        """
        # Business rule: Validate transaction exists for this account
        transaction = self.transaction_repo.get_by_id(transaction_id, account)
        if not transaction:
            return None, "Transaction not found"

        # Business rule: Only allow updating specific fields
        allowed_fields = ["amount", "date"]
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not filtered_data:
            return None, "No updatable fields provided"

        # Update via repository
        updated_transaction = self.transaction_repo.update_transaction(
            transaction, **filtered_data
        )
        return updated_transaction, None

    def delete_transaction_and_recompute_balance(
        self, account, transaction_id: int
    ) -> tuple[bool, str | None]:
        """
        Delete a transaction and recalculate account balance.

        Business logic: After deletion, finds the new latest transaction
        and updates the account's balance accordingly.

        Args:
            account: Account instance
            transaction_id: Transaction ID to delete

        Returns:
            Tuple of (success boolean, error message or None)
        """
        # Business rule: Validate transaction exists
        transaction = self.transaction_repo.get_by_id(transaction_id, account)
        if not transaction:
            return False, "Transaction not found"

        # Delete transaction
        self.transaction_repo.delete_transaction(transaction)

        # Business rule: Recalculate account balance
        self._recalculate_account_balance(account)

        return True, None

    def get_paginated_transactions(
        self, account, page: int = 1, page_size: int = 10
    ) -> dict:
        """
        Get paginated transactions for an account with formatting.

        Business logic: Handles pagination logic and formats data for display.

        Args:
            account: Account instance
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with columns, rows, and pagination metadata
        """
        # Business rule: Validate pagination parameters
        page = max(1, page)
        page_size = max(1, min(100, page_size))

        # Get paginated transactions
        transactions = self.transaction_repo.get_account_transactions_paginated(
            account, page, page_size
        )
        total = self.transaction_repo.count_transactions(account)

        # Format for display
        rows = [
            {
                "id": t.id,
                "date": format_date(t.date),
                "amount": format_currency(t.amount),
            }
            for t in transactions
        ]

        return {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "amount", "title": "Amount"},
            ],
            "rows": rows,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def get_user_transactions_formatted(self, user, limit: int | None = None) -> dict:
        """
        Get all transactions for all user's accounts with formatting.

        Business logic: Formats transaction data for display.

        Args:
            user: User instance
            limit: Optional limit on number of transactions

        Returns:
            Dictionary with columns and rows for table display
        """
        transactions = self.transaction_repo.get_user_transactions_limited(user, limit)

        rows = [
            {
                "id": t.id,
                "date": format_date(t.date),
                "amount": format_currency(t.amount),
                "account": t.account.name,
            }
            for t in transactions
        ]

        return {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "amount", "title": "Amount"},
                {"field": "account", "title": "Account"},
            ],
            "rows": rows,
        }

    def _recalculate_account_balance(self, account) -> None:
        """
        Recalculate account balance from latest transaction.

        Business logic: Finds the most recent transaction and updates
        account balance, or sets to 0 if no transactions exist.

        Args:
            account: Account instance
        """
        latest = self.transaction_repo.get_latest_transaction(account)

        if latest:
            self.account_repo.update_latest_balance(account, latest.amount, latest.date)
        else:
            # No transactions - reset balance to 0
            self.account_repo.update_latest_balance(account, Decimal("0"), None)
