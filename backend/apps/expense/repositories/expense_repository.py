"""Repository for managing Expense data access."""

from datetime import date
from decimal import Decimal

from django.db.models import F, QuerySet, Sum
from django.db.models.functions import Coalesce
from apps.expense.models import Expense


class ExpenseRepository:
    """Repository for managing Expense data access - ORM layer only."""

    def get_by_id(self, expense_id: int, user) -> Expense | None:
        """Get an expense by ID with user ownership check."""
        try:
            return Expense.objects.get(id=expense_id, user=user)
        except Expense.DoesNotExist:
            return None

    def get_user_expenses(
        self, user, start_date: date | None = None, end_date: date | None = None
    ) -> QuerySet[Expense]:
        """
        Get all expenses for user with optional date filtering.

        Args:
            user: User instance
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            QuerySet of Expense entries
        """
        qs = Expense.objects.filter(user=user)

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        return qs

    def get_user_expenses_annotated(
        self, user, start_date: date | None = None, end_date: date | None = None
    ) -> QuerySet:
        """
        Get user expenses with annotated account and category names.

        Annotates:
            - Account: from account_name.name
            - Category: from category.name

        Returns ordered by date descending.
        """
        qs = Expense.objects.filter(user=user)

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        return (
            qs.annotate(
                Account=F("account_name__name"),
                Category=F("category__name"),
            )
            .order_by("-date")
            .values("id", "date", "description", "amount", "Account", "Category")
        )

    def get_user_expenses_limited(
        self, user, limit: int | None = None
    ) -> QuerySet[Expense]:
        """Get user expenses with optional limit."""
        qs = Expense.objects.filter(user=user).order_by("-date")
        if limit is not None:
            return qs[:limit]
        return qs

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

    def get_expenses_grouped_by_day(
        self, user, start_date: date, end_date: date
    ) -> dict[date, Decimal]:
        """
        Get expenses grouped by day for a date range.

        Returns dictionary mapping date to total expenses for that day.
        """
        expense_entries = Expense.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).order_by("date")

        # Group by date
        daily_totals: dict[date, Decimal] = {}
        for entry in expense_entries:
            if entry.date not in daily_totals:
                daily_totals[entry.date] = Decimal("0")
            daily_totals[entry.date] += entry.amount

        return daily_totals

    def get_expenses_grouped_by_month(
        self, user, start_date: date, end_date: date
    ) -> dict[tuple[int, int], Decimal]:
        """
        Get expenses grouped by month for a date range.

        Returns dictionary mapping (year, month) to total expenses for that month.
        """
        expense_entries = Expense.objects.filter(
            user=user, date__gte=start_date, date__lte=end_date
        ).order_by("date")

        # Group by month
        monthly_totals: dict[tuple[int, int], Decimal] = {}
        for entry in expense_entries:
            month_key = (entry.date.year, entry.date.month)
            if month_key not in monthly_totals:
                monthly_totals[month_key] = Decimal("0")
            monthly_totals[month_key] += entry.amount

        return monthly_totals

    def get_expenses_by_category(
        self, user, start_date: date, end_date: date, limit: int | None = None
    ) -> QuerySet:
        """
        Get expenses grouped by category for a date range.

        Returns QuerySet with category__name and total fields.
        """
        qs = (
            Expense.objects.filter(user=user, date__gte=start_date, date__lte=end_date)
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        if limit:
            qs = qs[:limit]

        return qs

    def get_existing_years_for_user(self, user) -> list[int]:
        """
        Get list of years where user has expenses.

        Returns:
            Sorted list of years
        """
        expenses = Expense.objects.filter(user=user, date__isnull=False)
        years = {expense.date.year for expense in expenses}
        return sorted(years)

    def create_expense(self, user, account, category, **expense_data) -> Expense:
        """Create a new expense."""
        return Expense.objects.create(
            user=user, account_name=account, category=category, **expense_data
        )

    def update_expense(self, expense: Expense, **data) -> Expense:
        """Update expense fields."""
        for key, value in data.items():
            setattr(expense, key, value)
        expense.save()
        return expense

    def delete_expense(self, expense: Expense) -> None:
        """Delete an expense."""
        expense.delete()
