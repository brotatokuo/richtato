"""Repository for Asset Dashboard data aggregation queries."""

from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.financial_account.models import FinancialAccount
from apps.transaction.models import Transaction


class AssetDashboardRepository:
    """Repository for Asset Dashboard aggregation queries - ORM layer only."""

    # Income queries (credit transactions)
    def get_earliest_income_date(self, user) -> date | None:
        """Get the earliest income date for user."""
        earliest = (
            Transaction.objects.filter(user=user, transaction_type="credit")
            .order_by("date")
            .first()
        )
        return earliest.date if earliest else None

    def get_income_sum_by_date_range(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of income (credit transactions) for a date range."""
        result = Transaction.objects.filter(
            user=user,
            transaction_type="credit",
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0")

    # Expense queries (debit transactions)
    def get_earliest_expense_date(self, user) -> date | None:
        """Get the earliest expense date for user."""
        earliest = (
            Transaction.objects.filter(user=user, transaction_type="debit")
            .order_by("date")
            .first()
        )
        return earliest.date if earliest else None

    def get_expense_sum_by_date_range(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of expenses (debit transactions) for a date range."""
        result = Transaction.objects.filter(
            user=user,
            transaction_type="debit",
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0")

    # Account queries
    def get_user_accounts(self, user):
        """Get all financial accounts for user."""
        return FinancialAccount.objects.filter(user=user, is_active=True)

    def get_networth(self, user) -> Decimal:
        """Calculate current networth (sum of all account balances)."""
        accounts = self.get_user_accounts(user)
        return sum(account.balance for account in accounts) or Decimal("0")

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
