"""Repository for managing Budget data access."""

from datetime import date
from decimal import Decimal

from django.db.models import F, Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from apps.budget.models import Budget


class BudgetRepository:
    """Repository for managing Budget data access - ORM layer only."""

    def get_by_id(self, budget_id: int, user) -> Budget | None:
        """Get a budget by ID with user ownership check."""
        try:
            return Budget.objects.select_related("category").get(
                id=budget_id, user=user
            )
        except Budget.DoesNotExist:
            return None

    def get_user_budgets(self, user) -> QuerySet[Budget]:
        """Get all budgets for user with optimized query."""
        return (
            Budget.objects.filter(user=user)
            .select_related("category")
            .order_by("-start_date")
        )

    def get_user_budgets_annotated(self, user, limit: int | None = None) -> QuerySet:
        """
        Get user budgets with annotated category name.

        Annotates:
            - category_name: from category.name

        Returns ordered by start_date descending.
        """
        qs = (
            Budget.objects.filter(user=user)
            .select_related("category")
            .order_by("-start_date")
            .values(
                "id",
                "start_date",
                "end_date",
                "amount",
                category_name=F("category__name"),
            )
        )

        if limit:
            qs = qs[:limit]

        return qs

    def get_active_budgets_for_date_range(
        self, user, start_date: date, end_date: date
    ) -> QuerySet[Budget]:
        """
        Get all budgets active during a date range.

        A budget is active if:
        - Its start_date is before or on the range end
        - Its end_date is None OR after or on the range start
        """
        return (
            Budget.objects.filter(
                user=user,
                start_date__lte=end_date,
            )
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=start_date))
            .select_related("category")
        )

    def get_overlapping_budgets(
        self,
        user,
        category,
        start_date: date,
        end_date: date | None,
        exclude_id: int | None = None,
    ) -> QuerySet[Budget]:
        """
        Find budgets that overlap with a given date range.

        Args:
            user: User instance
            category: Category instance
            start_date: Start date of range to check
            end_date: End date of range (None = infinite)
            exclude_id: Budget ID to exclude (for update operations)

        Returns:
            QuerySet of overlapping budgets
        """
        qs = Budget.objects.filter(user=user, category=category)

        if exclude_id:
            qs = qs.exclude(pk=exclude_id)

        return qs

    def create_budget(self, user, category, **budget_data) -> Budget:
        """Create a new budget."""
        return Budget.objects.create(user=user, category=category, **budget_data)

    def update_budget(self, budget: Budget, **data) -> Budget:
        """Update budget fields."""
        for key, value in data.items():
            setattr(budget, key, value)
        budget.save()
        return budget

    def delete_budget(self, budget: Budget) -> None:
        """Delete a budget."""
        budget.delete()

    def budget_exists_for_category(
        self, user, category, exclude_id: int | None = None
    ) -> bool:
        """
        Check if a budget already exists for a user/category combination.

        Args:
            user: User instance
            category: Category instance
            exclude_id: Budget ID to exclude (for update operations)

        Returns:
            True if budget exists, False otherwise
        """
        qs = Budget.objects.filter(user=user, category=category)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()
