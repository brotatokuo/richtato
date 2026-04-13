"""Repository for Annual Analysis data aggregation queries."""

from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum

from apps.core.constants import get_expense_filter, get_income_filter
from apps.transaction.models import Transaction


class AnnualAnalysisRepository:
    """Repository for Annual Analysis aggregation queries - ORM layer only."""

    def _get_expense_filter(self):
        return get_expense_filter()

    def _get_income_filter(self):
        return get_income_filter()

    def _tx_base(self, user, user_ids: list[int] | None = None):
        """Return base Transaction queryset scoped to user or household shared accounts."""
        if user_ids and len(user_ids) > 1:
            return Transaction.objects.filter(user_id__in=user_ids, account__shared_with_household=True)
        return Transaction.objects.filter(user=user)

    def get_expense_sum(self, user, start_date: date, end_date: date, user_ids: list[int] | None = None) -> Decimal:
        """Get sum of all expenses for a date range."""
        result = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date)
            .filter(self._get_expense_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_income_sum(self, user, start_date: date, end_date: date, user_ids: list[int] | None = None) -> Decimal:
        """Get sum of all income for a date range."""
        result = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date)
            .filter(self._get_income_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_essential_expense_sum(self, user, start_date: date, end_date: date, user_ids: list[int] | None = None) -> Decimal:
        """Get sum of essential expenses for a date range."""
        result = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date, category__expense_priority="essential")
            .filter(self._get_expense_filter())
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_non_essential_expense_sum(self, user, start_date: date, end_date: date, user_ids: list[int] | None = None) -> Decimal:
        """Get sum of non-essential expenses for a date range.

        Includes expenses where expense_priority is 'non_essential' or null.
        """
        result = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date)
            .filter(self._get_expense_filter())
            .filter(Q(category__expense_priority="non_essential") | Q(category__expense_priority__isnull=True))
            .aggregate(total=Sum("amount"))
        )
        return result["total"] or Decimal("0")

    def get_expenses_by_category_with_priority(self, user, start_date: date, end_date: date, user_ids: list[int] | None = None) -> list[dict]:
        """Get expenses grouped by category with essential/non-essential flag."""
        queryset = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date)
            .filter(self._get_expense_filter())
            .values(
                "category__name",
                "category__expense_priority",
                "category__color",
                "category__icon",
            )
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        return [
            {
                "name": item["category__name"] or "Uncategorized",
                "amount": float(item["total"]),
                "is_essential": item["category__expense_priority"] == "essential",
                "color": item["category__color"] or "#6b7280",
                "icon": item["category__icon"] or "",
            }
            for item in queryset
        ]

    def get_income_by_category(self, user, start_date: date, end_date: date, user_ids: list[int] | None = None) -> list[dict]:
        """Get income grouped by category."""
        queryset = (
            self._tx_base(user, user_ids)
            .filter(date__gte=start_date, date__lte=end_date)
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

    def get_transaction_years(self, user, user_ids: list[int] | None = None) -> list[int]:
        """Get list of years where user has transactions."""
        date_list = self._tx_base(user, user_ids).dates("date", "year", order="DESC")
        return [d.year for d in date_list]
