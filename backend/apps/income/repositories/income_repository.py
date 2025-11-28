"""Repository for managing Income data access."""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import F, QuerySet, Sum
from apps.income.models import Income


class IncomeRepository:
    """Repository for managing Income data access - ORM layer only."""

    def get_by_id(self, income_id: int, user) -> Income | None:
        """Get an income entry by ID with user ownership check."""
        try:
            return Income.objects.get(id=income_id, user=user)
        except Income.DoesNotExist:
            return None

    def get_user_income(
        self, user, start_date: date | None = None, end_date: date | None = None
    ) -> QuerySet[Income]:
        """
        Get all income entries for user with optional date filtering.

        Args:
            user: User instance
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            QuerySet of Income entries
        """
        qs = Income.objects.filter(user=user)

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        return qs

    def get_user_income_annotated(
        self, user, start_date: date | None = None, end_date: date | None = None
    ) -> QuerySet:
        """
        Get user income entries with annotated account name.

        Annotates:
            - Account: from account_name.name

        Returns ordered by date descending.
        """
        qs = Income.objects.filter(user=user)

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        return (
            qs.annotate(Account=F("account_name__name"))
            .order_by("-date")
            .values("id", "date", "Account", "description", "amount")
        )

    def get_user_income_limited(
        self, user, limit: int | None = None
    ) -> QuerySet[Income]:
        """Get user income entries with optional limit."""
        qs = Income.objects.filter(user=user).order_by("-date")
        if limit is not None:
            return qs[:limit]
        return qs

    def get_income_sum_by_date_range(
        self, user, start_date: date, end_date: date
    ) -> Decimal:
        """
        Get sum of income for a date range.

        Args:
            user: User instance
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Sum of income amount or 0
        """
        result = Income.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0")

    def get_income_by_month(self, user, year: int, month: int) -> QuerySet[Income]:
        """
        Get all income entries for a specific month.

        Args:
            user: User instance
            year: Year
            month: Month (1-12)

        Returns:
            QuerySet of Income entries
        """
        # Calculate first and last day of month
        from calendar import monthrange

        start_date = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        return Income.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        )

    def get_income_grouped_by_day(
        self, user, start_date: date, end_date: date
    ) -> dict[date, Decimal]:
        """
        Get income grouped by day for a date range.

        Returns dictionary mapping date to total income for that day.
        """
        income_entries = Income.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).order_by("date")

        # Group by date
        daily_totals: dict[date, Decimal] = {}
        for entry in income_entries:
            if entry.date not in daily_totals:
                daily_totals[entry.date] = Decimal("0")
            daily_totals[entry.date] += entry.amount

        return daily_totals

    def get_income_grouped_by_month(
        self, user, start_date: date, end_date: date
    ) -> dict[tuple[int, int], Decimal]:
        """
        Get income grouped by month for a date range.

        Returns dictionary mapping (year, month) to total income for that month.
        """
        income_entries = Income.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).order_by("date")

        # Group by month
        monthly_totals: dict[tuple[int, int], Decimal] = {}
        for entry in income_entries:
            month_key = (entry.date.year, entry.date.month)
            if month_key not in monthly_totals:
                monthly_totals[month_key] = Decimal("0")
            monthly_totals[month_key] += entry.amount

        return monthly_totals

    def create_income(self, user, **income_data) -> Income:
        """Create a new income entry."""
        return Income.objects.create(user=user, **income_data)

    def update_income(self, income: Income, **data) -> Income:
        """Update income fields."""
        for key, value in data.items():
            setattr(income, key, value)
        income.save()
        return income

    def delete_income(self, income: Income) -> None:
        """Delete an income entry."""
        income.delete()
