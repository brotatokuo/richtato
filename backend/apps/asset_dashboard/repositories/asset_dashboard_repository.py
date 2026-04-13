"""Repository for Asset Dashboard data aggregation queries."""

import bisect
from collections import defaultdict
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum

from apps.core.constants import get_expense_filter, get_income_filter, get_investment_filter
from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.transaction.models import Transaction


class AssetDashboardRepository:
    """Repository for Asset Dashboard aggregation queries - ORM layer only."""

    def _get_income_filter(self):
        return get_income_filter()

    def _get_expense_filter(self):
        return get_expense_filter()

    def _get_investment_filter(self):
        return get_investment_filter()

    # Income queries (based on category.is_income or credit transactions)
    def get_earliest_income_date(self, user) -> date | None:
        """Get the earliest income date for user."""
        earliest = Transaction.objects.filter(user=user).filter(self._get_income_filter()).order_by("date").first()
        return earliest.date if earliest else None

    def get_income_sum_by_date_range(self, user, start_date: date, end_date: date) -> Decimal:
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
        earliest = Transaction.objects.filter(user=user).filter(self._get_expense_filter()).order_by("date").first()
        return earliest.date if earliest else None

    def get_expense_sum_by_date_range(self, user, start_date: date, end_date: date) -> Decimal:
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

    def get_investment_sum_by_date_range(self, user, start_date: date, end_date: date) -> Decimal:
        """Get sum of investment transactions for a date range."""
        result = (
            Transaction.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            )
            .filter(self._get_investment_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    # Account queries
    def get_user_accounts(self, user):
        """Get all financial accounts for user."""
        return FinancialAccount.objects.filter(user=user, is_active=True)

    def get_user_asset_accounts(self, user):
        """Get all asset accounts for user (excluding liabilities like credit cards)."""
        return FinancialAccount.objects.filter(user=user, is_active=True, is_liability=False)

    def get_user_liability_accounts(self, user):
        """Get all liability accounts for user (e.g., credit cards)."""
        return FinancialAccount.objects.filter(user=user, is_active=True, is_liability=True)

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
        entry = AccountBalanceHistory.objects.filter(account=account, date__lte=target_date).order_by("-date").first()
        return entry.balance if entry else account.balance

    def get_networth_history(self, user, period: str = "6m") -> list[dict]:
        """
        Get net worth history over time based on AccountBalanceHistory records.

        Returns list of {date, networth, assets, liabilities} for each date
        where we have balance history records.

        Uses bulk queries to avoid N+1: fetches all account history in 2 DB
        queries, then resolves "balance at date" in Python via binary search.
        """
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

        # Single query for all active accounts
        all_accounts = list(
            FinancialAccount.objects.filter(user=user, is_active=True).values("id", "balance", "is_liability")
        )
        if not all_accounts:
            return []

        account_ids = [a["id"] for a in all_accounts]
        account_defaults = {a["id"]: a["balance"] for a in all_accounts}

        # Single query for all balance history up to end_date.
        # We intentionally fetch records older than start_date too so that
        # "balance at start of period" correctly resolves to the last known
        # balance before the window, rather than falling back to current balance.
        all_history_qs = (
            AccountBalanceHistory.objects.filter(account_id__in=account_ids, date__lte=end_date)
            .order_by("account_id", "date")
            .values("account_id", "date", "balance")
        )

        # Build per-account sorted lists for binary-search lookups
        account_dates: dict[int, list] = defaultdict(list)
        account_balances: dict[int, list] = defaultdict(list)
        for entry in all_history_qs:
            aid = entry["account_id"]
            account_dates[aid].append(entry["date"])
            account_balances[aid].append(entry["balance"])

        def balance_at_date(account_id: int, target_date: date) -> Decimal:
            dates = account_dates.get(account_id)
            if not dates:
                return account_defaults[account_id]
            idx = bisect.bisect_right(dates, target_date) - 1
            if idx < 0:
                return account_defaults[account_id]
            return account_balances[account_id][idx]

        # Unique dates within the requested period only
        all_dates_in_period = set()
        for aid in account_ids:
            for d in account_dates.get(aid, []):
                if start_date is None or d >= start_date:
                    all_dates_in_period.add(d)
        unique_dates = sorted(all_dates_in_period)

        history = []
        for record_date in unique_dates:
            total_assets = Decimal("0")
            total_liabilities = Decimal("0")
            for account in all_accounts:
                bal = balance_at_date(account["id"], record_date)
                if account["is_liability"]:
                    total_liabilities += abs(bal)
                else:
                    total_assets += bal

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
