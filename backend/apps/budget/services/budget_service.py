"""Service for budget management business logic."""

from datetime import date
from decimal import Decimal

from loguru import logger

from apps.budget.models import Budget, BudgetCategory
from apps.richtato_user.models import User
from apps.transaction.models import TransactionCategory


class BudgetService:
    """Service for budget management."""

    def get_user_budgets(self, user: User, active_only: bool = True) -> list[Budget]:
        """Get all budgets for a user."""
        queryset = Budget.objects.filter(user=user).prefetch_related("budget_categories", "budget_categories__category")
        if active_only:
            queryset = queryset.filter(is_active=True)
        return list(queryset.all())

    def get_household_budgets(self, user_ids: list[int], active_only: bool = True) -> list[Budget]:
        """Get household-level budgets for any of the given user IDs."""
        queryset = Budget.objects.filter(
            user_id__in=user_ids, is_household=True,
        ).prefetch_related("budget_categories", "budget_categories__category")
        if active_only:
            queryset = queryset.filter(is_active=True)
        return list(queryset.all())

    def get_budget_by_id(self, budget_id: int, user: User) -> Budget | None:
        """Get budget by ID, ensuring it belongs to the user."""
        try:
            return Budget.objects.prefetch_related("budget_categories", "budget_categories__category").get(
                id=budget_id, user=user
            )
        except Budget.DoesNotExist:
            return None

    def get_current_budget(self, user: User) -> Budget | None:
        """Get the currently active budget for the user."""
        today = date.today()
        try:
            return Budget.objects.filter(
                user=user,
                is_active=True,
                start_date__lte=today,
                end_date__gte=today,
            ).first()
        except Budget.DoesNotExist:
            return None

    def create_budget(
        self,
        user: User,
        name: str,
        period_type: str,
        start_date: date,
        end_date: date,
        categories_data: list[dict] = None,
    ) -> Budget:
        """
        Create a new budget.

        Args:
            user: Budget owner
            name: Budget name
            period_type: 'monthly', 'yearly', or 'custom'
            start_date: Period start
            end_date: Period end
            categories_data: List of dicts with category_id and allocated_amount

        Returns:
            Created Budget instance
        """
        budget = Budget.objects.create(
            user=user,
            name=name,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
        )

        # Add categories if provided
        if categories_data:
            for cat_data in categories_data:
                category = TransactionCategory.objects.get(id=cat_data["category_id"])
                BudgetCategory.objects.create(
                    budget=budget,
                    category=category,
                    allocated_amount=cat_data["allocated_amount"],
                    rollover_enabled=cat_data.get("rollover_enabled", False),
                )

        logger.info(f"Created budget {budget.id} for user {user.username}: {name}")

        return budget

    def create_monthly_budget(
        self, user: User, name: str, year: int, month: int, categories_data: list[dict]
    ) -> Budget:
        """
        Create a monthly budget.

        Args:
            user: Budget owner
            name: Budget name
            year: Year
            month: Month (1-12)
            categories_data: List of category allocations

        Returns:
            Created Budget instance
        """
        from calendar import monthrange

        start_date = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        return self.create_budget(user, name, "monthly", start_date, end_date, categories_data)

    def add_budget_category(
        self,
        budget: Budget,
        category: TransactionCategory,
        allocated_amount: Decimal,
        rollover_enabled: bool = False,
    ) -> BudgetCategory:
        """Add a category allocation to a budget."""
        budget_category = BudgetCategory.objects.create(
            budget=budget,
            category=category,
            allocated_amount=allocated_amount,
            rollover_enabled=rollover_enabled,
        )

        logger.info(f"Added category {category.name} to budget {budget.id}: ${allocated_amount}")

        return budget_category

    def update_budget_category(self, budget_category: BudgetCategory, **kwargs) -> BudgetCategory:
        """Update a budget category allocation."""
        for key, value in kwargs.items():
            if hasattr(budget_category, key):
                setattr(budget_category, key, value)
        budget_category.save()
        return budget_category

    def delete_budget(self, budget: Budget) -> bool:
        """Delete (deactivate) a budget."""
        try:
            budget.is_active = False
            budget.save()
            logger.info(f"Deactivated budget {budget.id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting budget {budget.id}: {str(e)}")
            return False

    def duplicate_budget(
        self,
        budget: Budget,
        new_start_date: date,
        new_end_date: date,
        new_name: str = None,
    ) -> Budget:
        """
        Duplicate an existing budget for a new period.

        Args:
            budget: Budget to duplicate
            new_start_date: Start date for new budget
            new_end_date: End date for new budget
            new_name: Optional new name (defaults to original name)

        Returns:
            New Budget instance
        """
        name = new_name or f"{budget.name} (Copy)"

        new_budget = Budget.objects.create(
            user=budget.user,
            name=name,
            period_type=budget.period_type,
            start_date=new_start_date,
            end_date=new_end_date,
        )

        # Copy all category allocations
        for budget_category in budget.budget_categories.all():
            BudgetCategory.objects.create(
                budget=new_budget,
                category=budget_category.category,
                allocated_amount=budget_category.allocated_amount,
                rollover_enabled=budget_category.rollover_enabled,
            )

        logger.info(f"Duplicated budget {budget.id} to new budget {new_budget.id}")

        return new_budget
