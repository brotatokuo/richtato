"""Service for calculating budget progress from transactions."""

from datetime import date
from decimal import Decimal
from typing import Dict, List

from apps.budget_v2.models import Budget, BudgetCategory, BudgetProgress
from apps.transaction.repositories.transaction_repository import TransactionRepository
from loguru import logger


class BudgetCalculationService:
    """Service for real-time budget progress calculation from transactions."""

    def __init__(self):
        self.transaction_repository = TransactionRepository()

    def calculate_budget_progress(self, budget: Budget) -> Dict:
        """
        Calculate complete progress for a budget across all categories.

        Args:
            budget: Budget to calculate progress for

        Returns:
            Dict with progress data
        """
        categories_progress = []
        total_allocated = Decimal("0")
        total_spent = Decimal("0")

        for budget_category in budget.budget_categories.select_related("category"):
            progress = self.calculate_category_progress(
                budget_category, budget.start_date, budget.end_date
            )
            categories_progress.append(progress)
            total_allocated += budget_category.total_available
            total_spent += progress["spent_amount"]

        return {
            "budget_id": budget.id,
            "budget_name": budget.name,
            "period": {
                "start": str(budget.start_date),
                "end": str(budget.end_date),
                "type": budget.period_type,
            },
            "totals": {
                "allocated": total_allocated,
                "spent": total_spent,
                "remaining": total_allocated - total_spent,
                "percentage_used": (
                    (total_spent / total_allocated * 100) if total_allocated > 0 else 0
                ),
            },
            "categories": categories_progress,
        }

    def calculate_category_progress(
        self, budget_category: BudgetCategory, start_date: date, end_date: date
    ) -> Dict:
        """
        Calculate progress for a specific budget category.

        Args:
            budget_category: BudgetCategory to calculate for
            start_date: Period start date
            end_date: Period end date

        Returns:
            Dict with category progress data
        """
        # Get all debit transactions for this category in the period
        transactions = self.transaction_repository.get_by_user(
            user=budget_category.budget.user,
            start_date=start_date,
            end_date=end_date,
            category=budget_category.category,
            transaction_type="debit",  # Only count expenses
        )

        # Calculate total spent
        spent_amount = sum(txn.amount for txn in transactions)
        transaction_count = len(transactions)

        # Calculate remaining and percentage
        total_available = budget_category.total_available
        remaining_amount = total_available - spent_amount
        percentage_used = (
            (spent_amount / total_available * 100) if total_available > 0 else 0
        )

        return {
            "budget_category_id": budget_category.id,
            "category": {
                "id": budget_category.category.id,
                "name": budget_category.category.name,
                "full_path": budget_category.category.full_path,
            },
            "allocated_amount": budget_category.allocated_amount,
            "rollover_amount": budget_category.rollover_amount,
            "total_available": total_available,
            "spent_amount": spent_amount,
            "remaining_amount": remaining_amount,
            "transaction_count": transaction_count,
            "percentage_used": float(percentage_used),
            "is_over_budget": spent_amount > total_available,
            "status": self._get_status(percentage_used),
        }

    def _get_status(self, percentage_used: Decimal) -> str:
        """Get status based on percentage used."""
        if percentage_used >= 100:
            return "over_budget"
        elif percentage_used >= 90:
            return "warning"
        elif percentage_used >= 75:
            return "caution"
        else:
            return "on_track"

    def update_cached_progress(
        self, budget_category: BudgetCategory, start_date: date, end_date: date
    ) -> BudgetProgress:
        """
        Update cached progress for a budget category.

        Args:
            budget_category: BudgetCategory to update
            start_date: Period start
            end_date: Period end

        Returns:
            Updated BudgetProgress instance
        """
        progress_data = self.calculate_category_progress(
            budget_category, start_date, end_date
        )

        progress, created = BudgetProgress.objects.update_or_create(
            budget_category=budget_category,
            period_start=start_date,
            period_end=end_date,
            defaults={
                "spent_amount": progress_data["spent_amount"],
                "remaining_amount": progress_data["remaining_amount"],
                "transaction_count": progress_data["transaction_count"],
            },
        )

        logger.info(
            f"{'Created' if created else 'Updated'} budget progress for "
            f"{budget_category}: ${progress_data['spent_amount']} / "
            f"${progress_data['total_available']}"
        )

        return progress

    def update_all_cached_progress(self, budget: Budget) -> List[BudgetProgress]:
        """
        Update cached progress for all categories in a budget.

        Args:
            budget: Budget to update

        Returns:
            List of updated BudgetProgress instances
        """
        progress_list = []

        for budget_category in budget.budget_categories.all():
            progress = self.update_cached_progress(
                budget_category, budget.start_date, budget.end_date
            )
            progress_list.append(progress)

        logger.info(f"Updated cached progress for {len(progress_list)} categories")

        return progress_list
