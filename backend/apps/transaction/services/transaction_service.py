"""Service for transaction business logic."""

from datetime import date
from decimal import Decimal

from django.db.models import QuerySet, Sum
from django.db.models.functions import Coalesce
from loguru import logger

from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import CategoryKeyword, Transaction, TransactionCategory
from apps.transaction.repositories.category_repository import CategoryRepository
from apps.transaction.repositories.transaction_repository import TransactionRepository


class TransactionService:
    """Service for transaction management business logic."""

    def __init__(self):
        self.transaction_repository = TransactionRepository()
        self.category_repository = CategoryRepository()

    def get_user_transactions(
        self,
        user: User,
        start_date: date | None = None,
        end_date: date | None = None,
        account: FinancialAccount | None = None,
        category: TransactionCategory | None = None,
        transaction_type: str | None = None,
    ) -> QuerySet[Transaction]:
        """Get transactions for a user with optional filters. Returns lazy queryset."""
        return self.transaction_repository.get_by_user(
            user=user,
            start_date=start_date,
            end_date=end_date,
            account=account,
            category=category,
            transaction_type=transaction_type,
        )

    def get_household_transactions(
        self,
        user_ids: list[int],
        start_date: date | None = None,
        end_date: date | None = None,
        category: TransactionCategory | None = None,
        transaction_type: str | None = None,
    ) -> QuerySet[Transaction]:
        """Get transactions from shared accounts for household members."""
        return self.transaction_repository.get_by_user_ids_shared(
            user_ids=user_ids,
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=transaction_type,
        )

    def get_transaction_by_id(self, transaction_id: int, user: User) -> Transaction | None:
        """Get transaction by ID, ensuring it belongs to the user."""
        transaction = self.transaction_repository.get_by_id(transaction_id)
        if transaction and transaction.user == user:
            return transaction
        return None

    def create_manual_transaction(
        self,
        user: User,
        account: FinancialAccount,
        date: date,
        amount: Decimal,
        description: str,
        transaction_type: str = "debit",
        category_id: int | None = None,
        status: str = "posted",
        notes: str | None = "",
    ) -> Transaction:
        """
        Create a manually entered transaction.

        Args:
            user: Transaction owner
            account: Financial account
            date: Transaction date
            amount: Transaction amount (always positive)
            description: Transaction description
            transaction_type: 'debit' or 'credit'
            category_id: Optional category ID
            status: Transaction status

        Returns:
            Created Transaction instance
        """
        # Get or create category if provided
        category = None
        if category_id:
            category = self.category_repository.get_by_id(category_id)
        else:
            matched_category = self._match_category_via_keywords(user, description)
            if matched_category:
                category = matched_category

        transaction = self.transaction_repository.create_transaction(
            user=user,
            account=account,
            date=date,
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            category=category,
            status=status,
            sync_source="manual",
            notes=notes,
        )

        logger.info(f"Created manual transaction {transaction.id} for user {user.username}: {description} ({amount})")

        return transaction

    def update_transaction(self, transaction: Transaction, **kwargs) -> Transaction:
        """Update transaction fields."""
        # Handle category_id separately
        if "category_id" in kwargs:
            category_id = kwargs.pop("category_id")
            if category_id:
                category = self.category_repository.get_by_id(category_id)
                kwargs["category"] = category
            else:
                kwargs["category"] = None

        return self.transaction_repository.update_transaction(transaction, **kwargs)

    def delete_transaction(self, transaction: Transaction) -> bool:
        """
        Delete a transaction.

        Args:
            transaction: Transaction to delete

        Returns:
            True if successful
        """
        try:
            self.transaction_repository.delete_transaction(transaction)
            logger.info(f"Deleted transaction {transaction.id}: {transaction.description}")
            return True
        except Exception as e:
            logger.error(f"Error deleting transaction {transaction.id}: {str(e)}")
            return False

    def search_transactions(self, user: User, search_term: str, limit: int = 50) -> list[Transaction]:
        """Search transactions by description."""
        return self.transaction_repository.search_transactions(user, search_term, limit)

    def get_uncategorized_transactions(self, user: User, limit: int = 100) -> list[Transaction]:
        """Get transactions without a category."""
        return self.transaction_repository.get_uncategorized_transactions(user, limit)

    def categorize_transaction(self, transaction: Transaction, category_id: int) -> Transaction:
        """
        Categorize a transaction.

        Args:
            transaction: Transaction to categorize
            category_id: Category ID to assign

        Returns:
            Updated transaction
        """
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        return self.transaction_repository.update_transaction(transaction, category=category)

    def get_transaction_summary(self, user: User, start_date: date, end_date: date) -> dict:
        """
        Get transaction summary for a date range.

        Args:
            user: User
            start_date: Start date
            end_date: End date

        Returns:
            Dict with summary data
        """
        transactions = list(self.get_user_transactions(user, start_date=start_date, end_date=end_date))

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        by_category = {}

        for txn in transactions:
            if txn.transaction_type == "credit":
                total_income += txn.amount
            else:
                total_expenses += txn.amount

            category_name = txn.category_name
            if category_name not in by_category:
                by_category[category_name] = {
                    "count": 0,
                    "total": Decimal("0"),
                }
            by_category[category_name]["count"] += 1
            by_category[category_name]["total"] += txn.amount

        return {
            "total_transactions": len(transactions),
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
            "by_category": by_category,
        }

    def get_cashflow_summary(self, user: User, start_date: date, end_date: date) -> dict:
        """
        Get cashflow summary for a date range using DB aggregation.
        Returns income/expense/investment totals by category without loading all transactions.
        """
        base = Transaction.objects.filter(user=user, date__gte=start_date, date__lte=end_date)

        # Income by category (credits only)
        income_agg = (
            base.filter(transaction_type="credit")
            .values("category__name")
            .annotate(total=Coalesce(Sum("amount"), Decimal("0")))
        )
        income_by_category = {}
        total_income = Decimal("0")
        for row in income_agg:
            name = row["category__name"] or "Other Income"
            amt = row["total"]
            income_by_category[name] = float(amt)
            total_income += amt

        # Debits: split into expenses vs investments by category type
        debit_agg = (
            base.filter(transaction_type="debit")
            .values("category__name", "category__type")
            .annotate(total=Coalesce(Sum("amount"), Decimal("0")))
        )
        expenses_by_category = {}
        investments_by_category = {}
        total_expenses = Decimal("0")
        total_investments = Decimal("0")

        for row in debit_agg:
            name = row["category__name"] or "Uncategorized"
            cat_type = row["category__type"] or ""
            amt = row["total"]
            is_investment = cat_type == "investment" or (name and "investment" in name.lower())
            if is_investment:
                total_investments += amt
                investments_by_category[name] = investments_by_category.get(name, 0) + float(amt)
            else:
                total_expenses += amt
                expenses_by_category[name] = expenses_by_category.get(name, 0) + float(amt)

        return {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "total_investments": float(total_investments),
            "net_savings": float(total_income - total_expenses - total_investments),
            "income_by_category": income_by_category,
            "expenses_by_category": expenses_by_category,
            "investments_by_category": investments_by_category,
        }

    def _match_category_via_keywords(self, user: User, description: str) -> TransactionCategory | None:
        """Try to match a category using user keyword rules."""
        text_parts = [description or ""]
        haystack = " ".join(text_parts).lower()

        # Query keywords for user's categories
        keywords = CategoryKeyword.objects.filter(user=user).select_related("category").order_by("-match_count")

        for keyword_obj in keywords:
            kw = keyword_obj.keyword.strip().lower()
            if kw and kw in haystack:
                return keyword_obj.category
        return None
