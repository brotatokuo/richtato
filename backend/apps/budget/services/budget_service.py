"""Service layer for Budget business logic."""

import calendar
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from utilities.tools import format_currency


class BudgetService:
    """Service for managing Budget business logic - no ORM calls."""

    def __init__(self, budget_repo, expense_repo, category_repo):
        """
        Initialize service with repository dependencies.

        Args:
            budget_repo: BudgetRepository instance
            expense_repo: ExpenseRepository instance (for budget progress calculations)
            category_repo: CategoryRepository instance
        """
        self.budget_repo = budget_repo
        self.expense_repo = expense_repo
        self.category_repo = category_repo

    def get_user_budgets_formatted(self, user, limit: int | None = None) -> dict:
        """
        Get user budgets with formatted data for API response.

        Business logic: Formats budget data for table display.

        Args:
            user: User instance
            limit: Optional limit on number of entries

        Returns:
            Dictionary with columns and rows for table display
        """
        budgets = self.budget_repo.get_user_budgets_annotated(user, limit)

        rows = [
            {
                "id": b["id"],
                "category": b["category_name"],
                "amount": b["amount"],
                "start_date": b["start_date"],
                "end_date": b["end_date"],
            }
            for b in budgets
        ]

        return {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "category", "title": "Category"},
                {"field": "amount", "title": "Amount"},
                {"field": "start_date", "title": "Start Date"},
                {"field": "end_date", "title": "End Date"},
            ],
            "rows": rows,
        }

    def validate_budget_dates(
        self, start_date: date, end_date: date | None
    ) -> tuple[bool, str | None]:
        """
        Validate budget date range.

        Business logic: Ensures start_date is before end_date.

        Args:
            start_date: Budget start date
            end_date: Budget end date (None = no end)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if end_date and start_date >= end_date:
            return False, "Start date must be before end date"
        return True, None

    def check_budget_overlap(
        self,
        user,
        category,
        start_date: date,
        end_date: date | None,
        exclude_budget_id: int | None = None,
    ) -> tuple[bool, str | None]:
        """
        Check if a budget overlaps with existing budgets.

        Business logic: Two date ranges overlap if start1 < end2 AND start2 < end1.

        Args:
            user: User instance
            category: Category instance
            start_date: New budget start date
            end_date: New budget end date (None = infinite)
            exclude_budget_id: Budget ID to exclude (for updates)

        Returns:
            Tuple of (has_overlap, error_message)
        """
        # Get all budgets for this user/category (excluding the current one if updating)
        overlapping_budgets = self.budget_repo.get_overlapping_budgets(
            user, category, start_date, end_date, exclude_budget_id
        )

        # Check each for overlap
        for budget in overlapping_budgets:
            if self._ranges_overlap(
                start_date, end_date, budget.start_date, budget.end_date
            ):
                return True, (
                    f"Budget overlaps with existing budget from "
                    f"{budget.start_date} to {budget.end_date or '∞'}"
                )

        return False, None

    def _ranges_overlap(
        self, start1: date, end1: date | None, start2: date, end2: date | None
    ) -> bool:
        """
        Check if two date ranges overlap.

        Business logic: Convert None end_dates to far future, then check:
        start1 < end2 AND start2 < end1

        Args:
            start1: First range start
            end1: First range end (None = infinite)
            start2: Second range start
            end2: Second range end (None = infinite)

        Returns:
            True if ranges overlap, False otherwise
        """
        # Convert None end_dates to far future for comparison
        end1_date = end1 or date(9999, 12, 31)
        end2_date = end2 or date(9999, 12, 31)

        # Two ranges overlap if: start1 < end2 AND start2 < end1
        return start1 < end2_date and start2 < end1_date

    def create_budget(
        self,
        user,
        category_id: int,
        start_date: date,
        end_date: date | None,
        amount: Decimal,
    ) -> tuple[object | None, str | None]:
        """
        Create a new budget with validation.

        Business logic:
        - Validates date range
        - Checks for overlaps
        - Validates category ownership

        Args:
            user: User instance
            category_id: Category ID
            start_date: Budget start date
            end_date: Budget end date (None = no end)
            amount: Budget amount

        Returns:
            Tuple of (budget instance or None, error message or None)
        """
        # Business rule: Validate dates
        valid, error = self.validate_budget_dates(start_date, end_date)
        if not valid:
            return None, error

        # Business rule: Validate category ownership
        category = self.category_repo.get_by_id(category_id, user)
        if not category:
            return None, "Category not found for user"

        # Business rule: Check for overlaps
        has_overlap, error = self.check_budget_overlap(
            user, category, start_date, end_date
        )
        if has_overlap:
            return None, error

        # Create budget via repository
        budget = self.budget_repo.create_budget(
            user=user,
            category=category,
            start_date=start_date,
            end_date=end_date,
            amount=amount,
        )
        return budget, None

    def update_budget(
        self, user, budget_id: int, data: dict
    ) -> tuple[object | None, str | None]:
        """
        Update an existing budget with validation.

        Business logic: Validates ownership, dates, and overlaps.

        Args:
            user: User instance
            budget_id: Budget ID to update
            data: Dictionary of fields to update

        Returns:
            Tuple of (updated budget or None, error message or None)
        """
        # Business rule: Check ownership
        budget = self.budget_repo.get_by_id(budget_id, user)
        if not budget:
            return None, "Budget not found"

        # Get updated dates (use existing if not provided)
        start_date = data.get("start_date", budget.start_date)
        end_date = data.get("end_date", budget.end_date)

        # Business rule: Validate dates
        valid, error = self.validate_budget_dates(start_date, end_date)
        if not valid:
            return None, error

        # Business rule: If updating category, check overlaps
        category = budget.category
        if "category" in data:
            category = self.category_repo.get_by_id(data["category"], user)
            if not category:
                return None, "Category not found for user"

        # Business rule: Check for overlaps (excluding this budget)
        has_overlap, error = self.check_budget_overlap(
            user, category, start_date, end_date, exclude_budget_id=budget_id
        )
        if has_overlap:
            return None, error

        # Update via repository
        if "category" in data:
            data["category"] = category
        updated_budget = self.budget_repo.update_budget(budget, **data)
        return updated_budget, None

    def delete_budget(self, user, budget_id: int) -> tuple[bool, str | None]:
        """
        Delete a budget with ownership validation.

        Args:
            user: User instance
            budget_id: Budget ID to delete

        Returns:
            Tuple of (success boolean, error message or None)
        """
        # Business rule: Check ownership
        budget = self.budget_repo.get_by_id(budget_id, user)
        if not budget:
            return False, "Budget not found"

        # Delete via repository
        self.budget_repo.delete_budget(budget)
        return True, None

    def get_budget_rankings(
        self, user, year: int, month: int, count: int | None = None
    ) -> list[dict]:
        """
        Get budget rankings showing spending vs budget for each category.

        Business logic: Calculates percentage of budget used and ranks by usage.

        Args:
            user: User instance
            year: Year for calculation
            month: Month for calculation (1-12)
            count: Optional limit on number of categories

        Returns:
            List of budget ranking dictionaries
        """
        # Calculate date range for the month
        start_of_month = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_of_month = date(year, month, last_day)

        # Get budgets active during this month
        budgets = self.budget_repo.get_active_budgets_for_date_range(
            user, start_of_month, end_of_month
        )

        budget_expenses = []
        for budget in budgets:
            # Get total expenses for this category during the month
            total_expense = self.expense_repo.get_category_expense_sum(
                user, budget.category, start_of_month, end_of_month
            )

            # Calculate percentage of budget used
            percent_budget = (
                round(total_expense / budget.amount * 100) if budget.amount else 0
            )

            # Calculate difference and message
            difference = total_expense - budget.amount
            message = self._calculate_budget_diff_message(difference, percent_budget)

            budget_expenses.append(
                {
                    "name": budget.category.name,
                    "budget": budget.amount,
                    "spent": total_expense,
                    "percent": percent_budget,
                    "message": message,
                }
            )

        # Sort by percentage used (highest first)
        rankings = sorted(budget_expenses, key=lambda x: x["percent"], reverse=True)

        if count:
            rankings = rankings[:count]

        return rankings

    def _calculate_budget_diff_message(self, difference: Decimal, percent: int) -> str:
        """
        Calculate budget difference message.

        Business logic: Formats message showing over/under budget.

        Args:
            difference: Amount over/under budget
            percent: Percentage of budget used

        Returns:
            Formatted message string
        """
        if difference <= 0:
            return f"{format_currency(abs(difference))} left ({percent}%)"
        else:
            return f"{format_currency(abs(difference))} over ({percent}%)"

    def get_budget_progress(
        self,
        user,
        year: int | None = None,
        month: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        Get budget progress for a date range.

        Business logic: Calculates spending vs budget for each category.

        Args:
            user: User instance
            year: Year (optional, defaults to current)
            month: Month (optional, defaults to current)
            start_date: Start date (optional, overrides year/month)
            end_date: End date (optional, overrides year/month)

        Returns:
            Dictionary with budget progress data
        """
        # Determine date range
        if start_date and end_date:
            # Use provided dates
            pass
        else:
            # Use year/month or default to current month
            today = date.today()
            year = year or today.year
            month = month or today.month
            start_date = date(year, month, 1)
            end_date = date(year, month, calendar.monthrange(year, month)[1])

        # Validate date range
        if end_date < start_date:
            return {"error": "end_date must be on/after start_date"}

        # Get active budgets for this period
        budgets = self.budget_repo.get_active_budgets_for_date_range(
            user, start_date, end_date
        )

        results = []
        for budget in budgets:
            # Get total expenses for this category during the period
            total_spent = self.expense_repo.get_category_expense_sum(
                user, budget.category, start_date, end_date
            )

            budget_amount = budget.amount or Decimal(0)
            percentage = (
                int(round((total_spent / budget_amount) * 100))
                if budget_amount > 0
                else 0
            )

            # Round monetary values to 2 decimals
            budget_amount_q = budget_amount.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            total_spent_q = total_spent.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            remaining_q = (budget_amount - total_spent).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            results.append(
                {
                    "category": budget.category.name,
                    "budget": float(budget_amount_q),
                    "spent": float(total_spent_q),
                    "percentage": percentage,
                    "remaining": float(remaining_q),
                    "year": year or start_date.year,
                    "month": month or start_date.month,
                }
            )

        # Sort by highest percentage to lowest
        results = sorted(results, key=lambda x: x["percentage"], reverse=True)

        return {
            "budgets": results,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    def get_field_choices(self, user) -> dict:
        """
        Get field choices for budget creation.

        Args:
            user: User instance

        Returns:
            Dictionary with category choices
        """
        categories = self.category_repo.get_user_categories(user).values("id", "name")
        return {
            "category": [
                {"value": cat["id"], "label": cat["name"]} for cat in categories
            ],
        }
