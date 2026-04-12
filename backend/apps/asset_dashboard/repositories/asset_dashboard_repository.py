"""Repository for Asset Dashboard data aggregation queries."""

from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.transaction.models import Transaction

# Canonical slug for Credit Card Payment category (excluded from expenses)
CC_PAYMENT_CATEGORY_SLUG = "credit-card-payment"


class AssetDashboardRepository:
    """Repository for Asset Dashboard aggregation queries - ORM layer only."""

    def _get_income_filter(self):
        """
        Get Q filter for income transactions.

        Income is determined by:
        1. Transactions with category type="income", OR
        2. Uncategorized credit transactions (fallback for backward compatibility)
        """
        return Q(category__type="income") | Q(
            category__isnull=True, transaction_type="credit"
        )

    def _get_expense_filter(self):
        """
        Get Q filter for expense transactions.

        Expense is determined by:
        1. Transactions with category type="expense", OR
        2. Uncategorized debit transactions (fallback for backward compatibility)

        Explicitly excludes Credit Card Payment category for safety.
        """
        expense_filter = Q(category__type="expense") | Q(
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
        """Get sum of income for a date range (based on category.type='income')."""
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
        """Get sum of expenses for a date range (based on category.type='expense')."""
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
        """Calculate current net worth (sum of all active account balances).

        Assets are positive, liabilities are negative, so the sum is net worth.
        """
        accounts = self.get_user_accounts(user)
        return sum(account.balance for account in accounts) or Decimal("0")

    def get_total_assets(self, user) -> Decimal:
        """Get total assets (checking, savings, etc.)."""
        asset_accounts = self.get_user_asset_accounts(user)
        return sum(account.balance for account in asset_accounts) or Decimal("0")

    def get_total_liabilities(self, user) -> Decimal:
        """Get total liabilities as a positive number for display.

        Liability balances are stored negative; this returns abs() for UI display.
        """
        liability_accounts = self.get_user_liability_accounts(user)
        return abs(sum(account.balance for account in liability_accounts) or Decimal("0"))

    def get_balance_at_date(self, account, target_date: date) -> Decimal:
        """Get account balance at a specific date using balance history.

        Looks up the most recent AccountBalanceHistory entry on or before
        the target date. Falls back to current account balance if no
        history exists.
        """
        entry = (
            AccountBalanceHistory.objects.filter(
                account=account, date__lte=target_date
            )
            .order_by("-date")
            .first()
        )
        return entry.balance if entry else account.balance

    def get_networth_history(self, user, period: str = "6m") -> list[dict]:
        """
        Get net worth history over time based on AccountBalanceHistory records.

        Returns list of {date, networth, assets, liabilities} for each date
        where we have balance history records.
        """
        # Calculate date range based on period
        end_date = date.today()
        if period == "1m":
            start_date = end_date - relativedelta(months=1)
        elif period == "3m":
            start_date = end_date - relativedelta(months=3)
        elif period == "6m":
            start_date = end_date - relativedelta(months=6)
        elif period == "1y":
            start_date = end_date - relativedelta(years=1)
        elif period == "all":
            start_date = None
        else:
            start_date = end_date - relativedelta(months=6)

        # Get all user accounts
        asset_accounts = self.get_user_asset_accounts(user)
        liability_accounts = self.get_user_liability_accounts(user)

        # Get all balance history entries
        balance_query = AccountBalanceHistory.objects.filter(
            account__user=user
        ).order_by("date")

        if start_date:
            balance_query = balance_query.filter(date__gte=start_date)

        balance_query = balance_query.filter(date__lte=end_date)

        # Get unique dates from balance history
        unique_dates = (
            balance_query.values_list("date", flat=True).distinct().order_by("date")
        )

        # For each date, calculate total assets and liabilities
        history = []
        for record_date in unique_dates:
            total_assets = Decimal("0")
            for account in asset_accounts:
                total_assets += self.get_balance_at_date(account, record_date)

            # Liability balances are stored negative; show as positive for display
            total_liabilities = Decimal("0")
            for account in liability_accounts:
                total_liabilities += abs(
                    self.get_balance_at_date(account, record_date)
                )

            history.append(
                {
                    "date": record_date.isoformat(),
                    "assets": float(total_assets),
                    "liabilities": float(total_liabilities),
                    "networth": float(total_assets - total_liabilities),
                }
            )

        return history

    def get_account_type_breakdown(self, user) -> list[dict]:
        """
        Get account balances grouped by account type.

        Returns list of {type, type_display, total, count, is_liability}
        """
        accounts = FinancialAccount.objects.filter(user=user, is_active=True)

        # Group by account type
        breakdown = {}
        for account in accounts:
            acc_type = account.account_type
            if acc_type not in breakdown:
                breakdown[acc_type] = {
                    "type": acc_type,
                    "type_display": account.get_account_type_display(),
                    "total": Decimal("0"),
                    "count": 0,
                    "is_liability": account.is_liability,
                }
            breakdown[acc_type]["total"] += abs(account.balance) if account.is_liability else account.balance
            breakdown[acc_type]["count"] += 1

        # Convert to list and float values
        result = []
        for data in breakdown.values():
            result.append(
                {
                    "type": data["type"],
                    "type_display": data["type_display"],
                    "total": float(data["total"]),
                    "count": data["count"],
                    "is_liability": data["is_liability"],
                }
            )

        return result
