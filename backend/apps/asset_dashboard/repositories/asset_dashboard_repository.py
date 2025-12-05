"""Repository for Asset Dashboard data aggregation queries."""

from datetime import date
from decimal import Decimal

from apps.financial_account.models import FinancialAccount
from apps.transaction.models import Transaction
from django.db.models import Q, Sum

# Canonical slug for Credit Card Payment category (excluded from expenses)
CC_PAYMENT_CATEGORY_SLUG = "credit-card-payment"


class AssetDashboardRepository:
    """Repository for Asset Dashboard aggregation queries - ORM layer only."""

    def _get_income_filter(self):
        """
        Get Q filter for income transactions.

        Income is determined by:
        1. Transactions with category marked as is_income=True, OR
        2. Uncategorized credit transactions (fallback for backward compatibility)
        """
        return Q(category__is_income=True) | Q(
            category__isnull=True, transaction_type="credit"
        )

    def _get_expense_filter(self):
        """
        Get Q filter for expense transactions.

        Expense is determined by:
        1. Transactions with category marked as is_expense=True, OR
        2. Uncategorized debit transactions (fallback for backward compatibility)

        Explicitly excludes Credit Card Payment category for safety.
        """
        expense_filter = Q(category__is_expense=True) | Q(
            category__isnull=True, transaction_type="debit"
        )
        # Explicitly exclude Credit Card Payment category
        cc_payment_exclusion = ~Q(category__slug=CC_PAYMENT_CATEGORY_SLUG)
        return expense_filter & cc_payment_exclusion

    # Income queries (based on category.is_income or credit transactions)
    def get_earliest_income_date(self, user) -> date | None:
        """Get the earliest income date for user."""
        earliest = (
            Transaction.objects.filter(user=user)
            .filter(self._get_income_filter())
            .order_by("date")
            .first()
        )
        return earliest.date if earliest else None

    def get_income_sum_by_date_range(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of income for a date range (based on category.is_income)."""
        result = (
            Transaction.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            )
            .filter(self._get_income_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    # Expense queries (based on category.is_expense or debit transactions)
    def get_earliest_expense_date(self, user) -> date | None:
        """Get the earliest expense date for user."""
        earliest = (
            Transaction.objects.filter(user=user)
            .filter(self._get_expense_filter())
            .order_by("date")
            .first()
        )
        return earliest.date if earliest else None

    def get_expense_sum_by_date_range(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of expenses for a date range (based on category.is_expense)."""
        result = (
            Transaction.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            )
            .filter(self._get_expense_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    # Account queries
    def get_user_accounts(self, user):
        """Get all financial accounts for user."""
        return FinancialAccount.objects.filter(user=user, is_active=True)

    def get_user_asset_accounts(self, user):
        """Get all asset accounts for user (excluding liabilities like credit cards)."""
        return FinancialAccount.objects.filter(
            user=user, is_active=True, is_liability=False
        )

    def get_user_liability_accounts(self, user):
        """Get all liability accounts for user (e.g., credit cards)."""
        return FinancialAccount.objects.filter(
            user=user, is_active=True, is_liability=True
        )

    def get_networth(self, user) -> Decimal:
        """
        Calculate current networth (sum of asset account balances only).

        Note: Credit card balances (liabilities) are tracked separately and
        not included in the net worth calculation.
        """
        asset_accounts = self.get_user_asset_accounts(user)
        return sum(account.balance for account in asset_accounts) or Decimal("0")

    def get_total_liabilities(self, user) -> Decimal:
        """Get total liabilities (credit card balances, etc.)."""
        liability_accounts = self.get_user_liability_accounts(user)
        return sum(account.balance for account in liability_accounts) or Decimal("0")

    def get_account_balance_before_date(self, account, before_date: date) -> Decimal:
        """Get account balance before a specific date by summing transactions."""
        # Sum all transactions before the date
        credits = Transaction.objects.filter(
            account=account, date__lt=before_date, transaction_type="credit"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        debits = Transaction.objects.filter(
            account=account, date__lt=before_date, transaction_type="debit"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return credits - debits
