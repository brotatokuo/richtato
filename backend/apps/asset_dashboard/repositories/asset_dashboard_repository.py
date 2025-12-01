"""Repository for Asset Dashboard data aggregation queries."""

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from apps.account.models import Account, AccountTransaction
from apps.expense.models import Expense
from apps.income.models import Income


class AssetDashboardRepository:
    """Repository for Asset Dashboard aggregation queries - ORM layer only."""

    # Income queries
    def get_earliest_income_date(self, user) -> date | None:
        """Get the earliest income date for user."""
        earliest = Income.objects.filter(user=user).order_by("date").first()
        return earliest.date if earliest else None

    def get_income_sum_by_date_range(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of income for a date range."""
        result = Income.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0")

    # Expense queries
    def get_earliest_expense_date(self, user) -> date | None:
        """Get the earliest expense date for user."""
        earliest = Expense.objects.filter(user=user).order_by("date").first()
        return earliest.date if earliest else None

    def get_expense_sum_by_date_range(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of expenses for a date range."""
        result = Expense.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0")

    # Account queries
    def get_user_accounts(self, user):
        """Get all accounts for user."""
        return Account.objects.filter(user=user)

    def get_networth(self, user) -> Decimal:
        """Calculate current networth (sum of all account balances)."""
        accounts = self.get_user_accounts(user)
        return sum(account.latest_balance for account in accounts) or Decimal("0")

    def get_account_balance_before_date(self, account, before_date: date) -> Decimal:
        """Get account balance before a specific date."""
        latest_transaction = (
            AccountTransaction.objects.filter(account=account, date__lt=before_date)
            .order_by("-date")
            .first()
        )
        return latest_transaction.amount if latest_transaction else Decimal("0")
