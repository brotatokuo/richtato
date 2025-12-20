"""Repository for Budget Dashboard data aggregation queries."""

from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum

from apps.budget.models import Budget
from apps.transaction.models import Transaction

# Canonical slug for Credit Card Payment category (excluded from expenses)
CC_PAYMENT_CATEGORY_SLUG = "credit-card-payment"


class BudgetDashboardRepository:
    """Repository for Budget Dashboard aggregation queries - ORM layer only."""

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

    # Expense queries (based on category.type='expense' or debit transactions)
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

    def get_expenses_by_category(
        self, user, start_date: date, end_date: date, limit: int | None = None
    ):
        """Get expenses grouped by category for a date range."""
        qs = (
            Transaction.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            )
            .filter(self._get_expense_filter())
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
        # When filtering by specific category, we trust the category's type
        result = Transaction.objects.filter(
            user=user,
            category=category,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0")

    def get_nonessential_expense_sum(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of non-essential expenses for a date range.

        Filters by category.type='expense' for categorized transactions
        or falls back to debit transactions for uncategorized.
        """
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

    def get_expense_years(self, user) -> list[int]:
        """Get list of years where user has expenses."""
        date_list = (
            Transaction.objects.filter(user=user)
            .filter(self._get_expense_filter())
            .dates("date", "year", order="DESC")
        )
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
