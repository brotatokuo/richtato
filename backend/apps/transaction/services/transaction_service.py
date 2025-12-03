"""Service for transaction business logic."""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory
from apps.transaction.repositories.category_repository import CategoryRepository
from apps.transaction.repositories.merchant_repository import MerchantRepository
from apps.transaction.repositories.transaction_repository import TransactionRepository
from loguru import logger


class TransactionService:
    """Service for transaction management business logic."""

    def __init__(self):
        self.transaction_repository = TransactionRepository()
        self.category_repository = CategoryRepository()
        self.merchant_repository = MerchantRepository()

    def get_user_transactions(
        self,
        user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account: Optional[FinancialAccount] = None,
        category: Optional[TransactionCategory] = None,
        transaction_type: Optional[str] = None,
    ) -> List[Transaction]:
        """Get transactions for a user with optional filters."""
        return self.transaction_repository.get_by_user(
            user=user,
            start_date=start_date,
            end_date=end_date,
            account=account,
            category=category,
            transaction_type=transaction_type,
        )

    def get_transaction_by_id(
        self, transaction_id: int, user: User
    ) -> Optional[Transaction]:
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
        category_id: Optional[int] = None,
        merchant_name: Optional[str] = None,
        status: str = "posted",
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
            merchant_name: Optional merchant name
            status: Transaction status

        Returns:
            Created Transaction instance
        """
        # Get or create category if provided
        category = None
        if category_id:
            category = self.category_repository.get_by_id(category_id)

        # Get or create merchant if provided
        merchant = None
        if merchant_name:
            merchant = self.merchant_repository.get_or_create_merchant(
                name=merchant_name
            )

        transaction = self.transaction_repository.create_transaction(
            user=user,
            account=account,
            date=date,
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            category=category,
            merchant=merchant,
            status=status,
            sync_source="manual",
        )

        logger.info(
            f"Created manual transaction {transaction.id} for user {user.username}: "
            f"{description} ({amount})"
        )

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

        # Handle merchant_name separately
        if "merchant_name" in kwargs:
            merchant_name = kwargs.pop("merchant_name")
            if merchant_name:
                merchant = self.merchant_repository.get_or_create_merchant(
                    name=merchant_name
                )
                kwargs["merchant"] = merchant
            else:
                kwargs["merchant"] = None

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
            logger.info(
                f"Deleted transaction {transaction.id}: {transaction.description}"
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting transaction {transaction.id}: {str(e)}")
            return False

    def search_transactions(
        self, user: User, search_term: str, limit: int = 50
    ) -> List[Transaction]:
        """Search transactions by description or merchant."""
        return self.transaction_repository.search_transactions(user, search_term, limit)

    def get_uncategorized_transactions(
        self, user: User, limit: int = 100
    ) -> List[Transaction]:
        """Get transactions without a category."""
        return self.transaction_repository.get_uncategorized_transactions(user, limit)

    def categorize_transaction(
        self, transaction: Transaction, category_id: int
    ) -> Transaction:
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

        return self.transaction_repository.update_transaction(
            transaction, category=category
        )

    def get_transaction_summary(
        self, user: User, start_date: date, end_date: date
    ) -> Dict:
        """
        Get transaction summary for a date range.

        Args:
            user: User
            start_date: Start date
            end_date: End date

        Returns:
            Dict with summary data
        """
        transactions = self.get_user_transactions(
            user, start_date=start_date, end_date=end_date
        )

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        by_category = {}

        for txn in transactions:
            if txn.transaction_type == "credit":
                total_income += txn.amount
            else:
                total_expenses += txn.amount

            # Group by category
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
