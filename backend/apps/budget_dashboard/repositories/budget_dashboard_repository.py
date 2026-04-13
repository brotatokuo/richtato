"""Repository for Budget Dashboard data aggregation queries."""

from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.budget.models import Budget
from apps.core.constants import get_expense_filter
from apps.transaction.models import Transaction


class BudgetDashboardRepository:
    """Repository for Budget Dashboard aggregation queries - ORM layer only."""

    def _get_expense_filter(self):
        return get_expense_filter()

    def _tx_base(self, user, user_ids: list[int] | None = None):
        """Return base Transaction queryset scoped to user or household shared accounts."""
        if user_ids and len(user_ids) > 1:
            return Transaction.objects.filter(user_id__in=user_ids, account__shared_with_household=True)
        return Transaction.objects.filter(user=user)

    # Expense queries (based on category.type='expense' or debit transactions)
    def get_expense_sum_by_date_range(
        self, user, start_date: date, end_date: date, user_ids: list[int] | None = None
    ) -> Decimal:
        """Get sum of expenses for a date range (based on category.type='expense')."""
        result = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date)
            .filter(self._get_expense_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_expenses_by_category(
        self, user, start_date: date, end_date: date, limit: int | None = None, user_ids: list[int] | None = None
    ):
        """Get expenses grouped by category for a date range."""
        qs = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date)
            .filter(self._get_expense_filter())
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        if limit:
            qs = qs[:limit]
        return qs

    def get_category_expense_sum(
        self, user, category, start_date: date, end_date: date, user_ids: list[int] | None = None
    ) -> Decimal:
        """Get sum of expenses for a specific category and date range."""
        result = (
            self._tx_base(user, user_ids)
            .filter(category=category, date__gte=start_date, date__lte=end_date)
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_nonessential_expense_sum(
        self, user, start_date: date, end_date: date, user_ids: list[int] | None = None
    ) -> Decimal:
        """Get sum of non-essential expenses for a date range.

        Filters by category.type='expense' for categorized transactions
        or falls back to debit transactions for uncategorized.
        """
        result = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date)
            .filter(self._get_expense_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_expense_years(self, user, user_ids: list[int] | None = None) -> list[int]:
        """Get list of years where user has expenses."""
        date_list = self._tx_base(user, user_ids).filter(self._get_expense_filter()).dates("date", "year", order="DESC")
        return [d.year for d in date_list]

    # Budget queries (using budget_v2)
    def get_active_budgets_for_date_range(self, user, start_date: date, end_date: date):
        """Get budgets active during a date range."""
        return Budget.objects.filter(
            user=user,
            start_date__lte=end_date,
            end_date__gte=start_date,
            is_active=True,
        ).prefetch_related("budget_categories__category")
