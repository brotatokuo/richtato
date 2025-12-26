"""Service layer for Budget Dashboard business logic."""

import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


class BudgetDashboardService:
    """Service for Budget Dashboard calculations and aggregations - no ORM calls."""

    def __init__(self, budget_dashboard_repo):
        """
        Initialize service with repository dependency.

        Args:
            budget_dashboard_repo: BudgetDashboardRepository instance
        """
        self.repo = budget_dashboard_repo

    def get_expense_categories_data(
        self,
        user,
        start_date: date | None = None,
        end_date: date | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> dict:
        """
        Generate expense breakdown by category for pie chart.

        Business logic: Determines date range and aggregates expenses.

        Args:
            user: User instance
            start_date: Optional start date
            end_date: Optional end date
            year: Optional year
            month: Optional month

        Returns:
            Dictionary with labels, datasets, and date range
        """
        # Business rule: Determine date range
        start_date, end_date = self._determine_date_range(
            start_date, end_date, year, month
        )

        # Get expenses by category
        expenses = self.repo.get_expenses_by_category(
            user, start_date, end_date, limit=6
        )

        labels = [exp["category__name"] or "Uncategorized" for exp in expenses]
        data = [float(exp["total"]) for exp in expenses]

        # Color palette
        colors = ["#98CC2C", "#4CAF50", "#81C784", "#A5D6A7", "#C8E6C9", "#E8F5E8"]

        return {
            "labels": labels,
            "datasets": [
                {
                    "data": data,
                    "backgroundColor": colors[: len(data)],
                    "borderWidth": 2,
                    "borderColor": "#fff",
                }
            ],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

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
        budgets = self.repo.get_active_budgets_for_date_range(
            user, start_date, end_date
        )

        results = []
        for budget in budgets:
            # Iterate through each budget category allocation
            for budget_category in budget.budget_categories.all():
                category = budget_category.category
                # Get total expenses for this category during the period
                total_spent = self.repo.get_category_expense_sum(
                    user, category, start_date, end_date
                )

                budget_amount = budget_category.allocated_amount or Decimal(0)
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
                        "category": category.name,
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
        budgets = self.repo.get_active_budgets_for_date_range(
            user, start_of_month, end_of_month
        )

        budget_expenses = []
        for budget in budgets:
            # Iterate through each budget category allocation
            for budget_category in budget.budget_categories.all():
                category = budget_category.category
                # Get total expenses for this category during the month
                total_expense = self.repo.get_category_expense_sum(
                    user, category, start_of_month, end_of_month
                )

                allocated_amount = budget_category.allocated_amount or Decimal(0)
                # Calculate percentage of budget used
                percent_budget = (
                    round(total_expense / allocated_amount * 100)
                    if allocated_amount
                    else 0
                )

                # Calculate difference and message
                difference = total_expense - allocated_amount
                message = self._calculate_budget_diff_message(
                    difference, percent_budget
                )

                budget_expenses.append(
                    {
                        "name": category.name,
                        "budget": allocated_amount,
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

    def get_budget_utilization(self, user, start_date: date, end_date: date) -> str:
        """
        Calculate budget utilization percentage.

        Business logic: Total Spent / Total Budget across all active budgets.

        Returns:
            Formatted string like "75%" or "N/A"
        """
        budgets = self.repo.get_active_budgets_for_date_range(
            user, start_date, end_date
        )

        total_budget = Decimal(0)
        total_spent = Decimal(0)

        for budget in budgets:
            # Iterate through each budget category allocation
            for budget_category in budget.budget_categories.all():
                allocated_amount = budget_category.allocated_amount or Decimal(0)
                if allocated_amount > 0:
                    total_budget += allocated_amount
                    cat_expense = self.repo.get_category_expense_sum(
                        user, budget_category.category, start_date, end_date
                    )
                    total_spent += Decimal(cat_expense)

        if total_budget > 0:
            utilization = (total_spent / total_budget) * Decimal(100)
            return f"{round(float(utilization), 1)}%"
        else:
            return "N/A"

    def get_nonessential_spending_pct(
        self, user, start_date: date, end_date: date
    ) -> float:
        """
        Calculate non-essential spending percentage.

        Business logic: Calculates percentage of expenses that are non-essential.

        Returns:
            Percentage as float (0-100)
        """
        total_expense = self.repo.get_expense_sum_by_date_range(
            user, start_date, end_date
        )
        nonessential_expense = self.repo.get_nonessential_expense_sum(
            user, start_date, end_date
        )

        if total_expense > 0:
            return round((nonessential_expense / total_expense) * 100, 1)
        else:
            return 0.0

    def get_expense_years(self, user) -> list[int]:
        """
        Get list of years where user has expenses.

        Business logic: Delegates to repository.

        Args:
            user: User instance

        Returns:
            List of years
        """
        return self.repo.get_expense_years(user)

    def _calculate_budget_diff_message(self, difference: Decimal, percent: int) -> str:
        """
        Calculate budget difference message.

        Business logic: Returns raw difference amount and percentage for frontend formatting.

        Args:
            difference: Amount over/under budget
            percent: Percentage of budget used

        Returns:
            Message string with raw amount
        """
        if difference <= 0:
            return f"{float(abs(difference))} left ({percent}%)"
        else:
            return f"{float(abs(difference))} over ({percent}%)"

    def get_budget_progress_multi_month(
        self,
        user,
        months: int = 12,
    ) -> dict:
        """
        Get budget progress for the last N months.

        Business logic: Aggregates budget progress data for multiple months
        to support timeline and trend visualizations.

        Args:
            user: User instance
            months: Number of months to fetch (default 12)

        Returns:
            Dictionary with monthly_data list and metadata
        """
        today = date.today()
        monthly_data = []

        for i in range(months - 1, -1, -1):
            # Calculate the target month (going backwards from current)
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1

            # Get budget progress for this month
            progress = self.get_budget_progress(user, year=year, month=month)

            # Calculate totals for this month
            budgets = progress.get("budgets", [])
            total_budget = sum(b.get("budget", 0) for b in budgets)
            total_spent = sum(b.get("spent", 0) for b in budgets)
            total_remaining = total_budget - total_spent
            percentage = (
                int(round((total_spent / total_budget) * 100))
                if total_budget > 0
                else 0
            )

            month_name = calendar.month_abbr[month]

            monthly_data.append(
                {
                    "year": year,
                    "month": month,
                    "month_name": month_name,
                    "label": f"{month_name} {year}",
                    "total_budget": round(total_budget, 2),
                    "total_spent": round(total_spent, 2),
                    "total_remaining": round(total_remaining, 2),
                    "percentage": percentage,
                    "categories": budgets,
                    "start_date": progress.get("start_date"),
                    "end_date": progress.get("end_date"),
                }
            )

        return {
            "monthly_data": monthly_data,
            "months_requested": months,
        }

    def _determine_date_range(
        self,
        start_date: date | None,
        end_date: date | None,
        year: int | None,
        month: int | None,
    ) -> tuple[date, date]:
        """
        Determine date range from various parameters.

        Business logic: Handles multiple input formats for date ranges.

        Returns:
            Tuple of (start_date, end_date)
        """
        today = date.today()

        if start_date and end_date:
            return start_date, end_date
        elif year and month:
            start = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end = date(year, month, last_day)
            return start, end
        else:
            # Default to current month
            start = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end = today.replace(day=last_day)
            return start, end
