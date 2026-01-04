"""Repository for Annual Analysis data aggregation queries."""

from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum

from apps.transaction.models import Transaction

# Canonical slug for Credit Card Payment category (excluded from expenses)
CC_PAYMENT_CATEGORY_SLUG = "credit-card-payment"


class AnnualAnalysisRepository:
    """Repository for Annual Analysis aggregation queries - ORM layer only."""

    def _get_expense_filter(self):
        """
        Get Q filter for expense transactions.

        Expense is determined by:
        1. Transactions with category type="expense", OR
        2. Uncategorized debit transactions (fallback for backward compatibility)

        Explicitly excludes Credit Card Payment category.
        """
        expense_filter = Q(category__type="expense") | Q(
            category__isnull=True, transaction_type="debit"
        )
        cc_payment_exclusion = ~Q(category__slug=CC_PAYMENT_CATEGORY_SLUG)
        return expense_filter & cc_payment_exclusion

    def _get_income_filter(self):
        """
        Get Q filter for income transactions.

        Income is determined by category type="income".
        """
        return Q(category__type="income")

    def get_expense_sum(self, user, start_date: date, end_date: date) -> Decimal:
        """Get sum of all expenses for a date range."""
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

    def get_income_sum(self, user, start_date: date, end_date: date) -> Decimal:
        """Get sum of all income for a date range."""
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

    def get_essential_expense_sum(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of essential expenses for a date range."""
        result = (
            Transaction.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
                category__expense_priority="essential",
            )
            .filter(self._get_expense_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_non_essential_expense_sum(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """Get sum of non-essential expenses for a date range.

        Includes expenses where expense_priority is 'non_essential' or null.
        """
        result = (
            Transaction.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            )
            .filter(self._get_expense_filter())
            .filter(
                Q(category__expense_priority="non_essential")
                | Q(category__expense_priority__isnull=True)
            )
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_expenses_by_category_with_priority(
        self, user, start_date: date, end_date: date
    ) -> list[dict]:
        """Get expenses grouped by category with essential/non-essential flag."""
        queryset = (
            Transaction.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            )
            .filter(self._get_expense_filter())
            .values("category__name", "category__expense_priority", "category__color")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        return [
            {
                "name": item["category__name"] or "Uncategorized",
                "amount": float(item["total"]),
                "is_essential": item["category__expense_priority"] == "essential",
                "color": item["category__color"] or "#6b7280",
            }
            for item in queryset
        ]

    def get_income_by_category(
        self, user, start_date: date, end_date: date
    ) -> list[dict]:
        """Get income grouped by category."""
        queryset = (
            Transaction.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date,
            )
            .filter(self._get_income_filter())
            .values("category__name", "category__color")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        return [
            {
                "name": item["category__name"] or "Other Income",
                "amount": float(item["total"]),
                "color": item["category__color"] or "#22c55e",
            }
            for item in queryset
        ]

    def get_transaction_years(self, user) -> list[int]:
        """Get list of years where user has transactions."""
        date_list = Transaction.objects.filter(user=user).dates(
            "date", "year", order="DESC"
        )
        return [d.year for d in date_list]
