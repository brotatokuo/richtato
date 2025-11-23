"""Temporary repository for Expense queries needed by Budget."""

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from apps.expense.models import Expense


class ExpenseRepository:
    """Temporary repository for Expense data access needed by Budget calculations."""

    def get_category_expense_sum(
        self, user, category, start_date: date, end_date: date
    ) -> Decimal:
        """
        Get sum of expenses for a category within a date range.

        Args:
            user: User instance
            category: Category instance
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Sum of expense amounts or Decimal(0)
        """
        total = Expense.objects.filter(
            user=user,
            category=category,
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(total=Coalesce(Sum("amount"), Decimal(0)))

        return total["total"]
