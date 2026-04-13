"""Repository for Transaction model."""

from datetime import date
from decimal import Decimal

from django.db.models import Q, QuerySet

from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory


class TransactionRepository:
    """Repository for transaction data access."""

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Get transaction by ID."""
        try:
            return Transaction.objects.select_related("account", "category", "user").get(id=transaction_id)
        except Transaction.DoesNotExist:
            return None

    def get_by_user(
        self,
        user: User,
        start_date: date | None = None,
        end_date: date | None = None,
        account: FinancialAccount | None = None,
        category: TransactionCategory | None = None,
        transaction_type: str | None = None,
    ) -> QuerySet[Transaction]:
        """Get transactions for a user with optional filters. Returns lazy queryset."""
        queryset = (
            Transaction.objects.filter(user=user).select_related("account", "category").order_by("-date", "-created_at")
        )

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if account:
            queryset = queryset.filter(account=account)
        if category:
            queryset = queryset.filter(category=category)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        return queryset

    def get_by_user_ids_shared(
        self,
        user_ids: list[int],
        start_date: date | None = None,
        end_date: date | None = None,
        category: TransactionCategory | None = None,
        transaction_type: str | None = None,
    ) -> QuerySet[Transaction]:
        """Get transactions from shared accounts for multiple users (household scope)."""
        queryset = (
            Transaction.objects.filter(
                user_id__in=user_ids,
                account__shared_with_household=True,
            )
            .select_related("account", "category", "user")
            .order_by("-date", "-created_at")
        )

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if category:
            queryset = queryset.filter(category=category)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        return queryset

    def get_by_account(
        self,
        account: FinancialAccount,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Transaction]:
        """Get transactions for a specific account."""
        queryset = Transaction.objects.filter(account=account).select_related("category")

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return list(queryset.all())

    def get_by_external_id(self, user: User, external_id: str, sync_source: str) -> Transaction | None:
        """Get transaction by external ID and sync source."""
        try:
            return Transaction.objects.get(user=user, external_id=external_id, sync_source=sync_source)
        except Transaction.DoesNotExist:
            return None

    def create_transaction(
        self,
        user: User,
        account: FinancialAccount,
        date: date,
        amount: Decimal,
        description: str,
        transaction_type: str = "debit",
        category: TransactionCategory | None = None,
        status: str = "posted",
        sync_source: str = "manual",
        external_id: str = "",
        raw_data: dict = None,
        is_recurring: bool = False,
        notes: str = "",
    ) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction.objects.create(
            user=user,
            account=account,
            date=date,
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            category=category,
            status=status,
            sync_source=sync_source,
            external_id=external_id,
            raw_data=raw_data,
            is_recurring=is_recurring,
            notes=notes,
        )
        return transaction

    def update_transaction(self, transaction: Transaction, **kwargs) -> Transaction:
        """Update transaction fields."""
        for key, value in kwargs.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)
        transaction.save()
        return transaction

    def delete_transaction(self, transaction: Transaction) -> None:
        """Delete a transaction."""
        transaction.delete()

    def search_transactions(self, user: User, search_term: str, limit: int = 50) -> list[Transaction]:
        """Search transactions by description."""
        return list(
            Transaction.objects.filter(
                Q(description__icontains=search_term),
                user=user,
            )
            .select_related("account", "category")
            .order_by("-date")[:limit]
        )

    def get_uncategorized_transactions(self, user: User, limit: int = 100) -> list[Transaction]:
        """Get transactions without a category."""
        return list(
            Transaction.objects.filter(user=user, category__isnull=True)
            .select_related("account")
            .order_by("-date")[:limit]
        )
