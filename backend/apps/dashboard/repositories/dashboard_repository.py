"""Repository for Dashboard data aggregation queries."""

from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from apps.account.models import Account, AccountTransaction
from apps.budget.models import Budget
from apps.expense.models import Expense
from apps.income.models import Income


class DashboardRepository:
    """Repository for Dashboard aggregation queries - ORM layer only."""

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

    def get_expenses_by_category(
        self, user, start_date: date, end_date: date, limit: int | None = None
    ):
        """Get expenses grouped by category for a date range."""
        qs = (
            Expense.objects.filter(user=user, date__gte=start_date, date__lte=end_date)
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        if limit:
            qs = qs[:limit]
        return qs

    def get_nonessential_expense_sum(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of non-essential expenses for a date range."""
        result = Expense.objects.filter(
            user=user,
            category__type="nonessential",
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0")

    # Budget queries
    def get_active_budgets_for_date_range(self, user, start_date: date, end_date: date):
        """Get budgets active during a date range."""
        return (
            Budget.objects.filter(user=user, start_date__lte=end_date)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=start_date))
            .select_related("category")
        )

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

    def get_expense_years(self, user) -> list[int]:
        """Get list of years where user has expenses."""
        date_list = Expense.objects.filter(user=user).dates(
            "date", "year", order="DESC"
        )
        return [d.year for d in date_list]
