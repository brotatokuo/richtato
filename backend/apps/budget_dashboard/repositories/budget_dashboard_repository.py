"""Repository for Budget Dashboard data aggregation queries."""

from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from apps.budget.models import Budget
from apps.expense.models import Expense


class BudgetDashboardRepository:
    """Repository for Budget Dashboard aggregation queries - ORM layer only."""

    # Expense queries
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

    def get_category_expense_sum(
        self, user, category, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of expenses for a specific category and date range."""
        result = Expense.objects.filter(
            user=user,
            category=category,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0")

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

    def get_expense_years(self, user) -> list[int]:
        """Get list of years where user has expenses."""
        date_list = Expense.objects.filter(user=user).dates(
            "date", "year", order="DESC"
        )
        return [d.year for d in date_list]

    # Budget queries
    def get_active_budgets_for_date_range(self, user, start_date: date, end_date: date):
        """Get budgets active during a date range."""
        return (
            Budget.objects.filter(user=user, start_date__lte=end_date)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=start_date))
            .select_related("category")
        )
