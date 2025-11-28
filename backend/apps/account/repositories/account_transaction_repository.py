"""Repository for managing AccountTransaction data access."""

from django.db.models import QuerySet
from apps.account.models import Account, AccountTransaction


class AccountTransactionRepository:
    """Repository for managing AccountTransaction data access - ORM layer only."""

    def get_by_id(
        self, transaction_id: int, account: Account
    ) -> AccountTransaction | None:
        """Get a transaction by ID for a specific account."""
        try:
            return AccountTransaction.objects.get(id=transaction_id, account=account)
        except AccountTransaction.DoesNotExist:
            return None

    def get_account_transactions(
        self, account: Account, order_by: str = "-date"
    ) -> QuerySet[AccountTransaction]:
        """Get all transactions for an account with ordering."""
        return AccountTransaction.objects.filter(account=account).order_by(order_by)

    def get_account_transactions_paginated(
        self, account: Account, page: int, page_size: int
    ) -> QuerySet[AccountTransaction]:
        """Get paginated transactions for an account."""
        start = (page - 1) * page_size
        end = start + page_size
        return AccountTransaction.objects.filter(account=account).order_by(
            "-date", "-id"
        )[start:end]

    def get_user_transactions(
        self, user, order_by: str = "-date"
    ) -> QuerySet[AccountTransaction]:
        """Get all transactions for all accounts owned by a user."""
        return AccountTransaction.objects.filter(account__user=user).order_by(order_by)

    def get_user_transactions_limited(
        self, user, limit: int | None = None
    ) -> QuerySet[AccountTransaction]:
        """Get user transactions with optional limit."""
        qs = AccountTransaction.objects.filter(account__user=user).order_by("-date")
        if limit is not None:
            return qs[:limit]
        return qs

    def get_latest_transaction(self, account: Account) -> AccountTransaction | None:
        """Get the most recent transaction for an account."""
        return (
            AccountTransaction.objects.filter(account=account)
            .order_by("-date", "-id")
            .first()
        )

    def create_transaction(self, account: Account, amount, date) -> AccountTransaction:
        """Create a new transaction (without business logic)."""
        return AccountTransaction.objects.create(
            account=account, amount=amount, date=date
        )

    def update_transaction(
        self, transaction: AccountTransaction, **data
    ) -> AccountTransaction:
        """Update transaction fields."""
        for key, value in data.items():
            setattr(transaction, key, value)
        transaction.save()
        return transaction

    def delete_transaction(self, transaction: AccountTransaction) -> None:
        """Delete a transaction."""
        transaction.delete()

    def count_transactions(self, account: Account) -> int:
        """Count total transactions for an account."""
        return AccountTransaction.objects.filter(account=account).count()
