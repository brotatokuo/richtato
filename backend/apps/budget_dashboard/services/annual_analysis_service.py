"""Service layer for Annual Analysis business logic."""

import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


class AnnualAnalysisService:
    """Service for Annual Analysis calculations and aggregations."""

    def __init__(self, annual_analysis_repo):
        """
        Initialize service with repository dependency.

        Args:
            annual_analysis_repo: AnnualAnalysisRepository instance
        """
        self.repo = annual_analysis_repo

    def get_annual_analysis(self, user, year: int, user_ids: list[int] | None = None) -> dict:
        """
        Generate comprehensive annual analysis data.

        Args:
            user: User instance
            year: Year to analyze
            user_ids: Optional list of user IDs for household scope

        Returns:
            Dictionary with annual analysis data for charts
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Get totals
        total_income = self.repo.get_income_sum(user, start_date, end_date, user_ids=user_ids)
        total_expenses = self.repo.get_expense_sum(user, start_date, end_date, user_ids=user_ids)
        essential_total = self.repo.get_essential_expense_sum(user, start_date, end_date, user_ids=user_ids)
        non_essential_total = self.repo.get_non_essential_expense_sum(user, start_date, end_date, user_ids=user_ids)

        # Get monthly breakdown
        monthly_breakdown = self._get_monthly_breakdown(user, year, user_ids=user_ids)

        # Get category breakdown
        category_breakdown = self.repo.get_expenses_by_category_with_priority(
            user, start_date, end_date, user_ids=user_ids
        )

        # Get income sources
        income_sources = self.repo.get_income_by_category(user, start_date, end_date, user_ids=user_ids)

        net_savings = total_income - total_expenses
        if total_income > 0:
            savings_rate = round((net_savings / total_income) * 100)
        else:
            savings_rate = 0

        return {
            "year": year,
            "total_income": self._to_float(total_income),
            "total_expenses": self._to_float(total_expenses),
            "essential_total": self._to_float(essential_total),
            "non_essential_total": self._to_float(non_essential_total),
            "net_savings": self._to_float(net_savings),
            "savings_rate": savings_rate,
            "monthly_breakdown": monthly_breakdown,
            "category_breakdown": category_breakdown,
            "income_sources": income_sources,
        }

    def _get_monthly_breakdown(self, user, year: int, user_ids: list[int] | None = None) -> list[dict]:
        """
        Get monthly spending breakdown for essential vs non-essential.

        Args:
            user: User instance
            year: Year to analyze
            user_ids: Optional list of user IDs for household scope

        Returns:
            List of monthly breakdowns
        """
        monthly_data = []

        for month in range(1, 13):
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)

            essential = self.repo.get_essential_expense_sum(user, start_date, end_date, user_ids=user_ids)
            non_essential = self.repo.get_non_essential_expense_sum(user, start_date, end_date, user_ids=user_ids)

            monthly_data.append(
                {
                    "month": calendar.month_abbr[month],
                    "month_num": month,
                    "essential": self._to_float(essential),
                    "non_essential": self._to_float(non_essential),
                    "total": self._to_float(essential + non_essential),
                }
            )

        return monthly_data

    def get_available_years(self, user, user_ids: list[int] | None = None) -> list[int]:
        """
        Get list of years with transaction data.

        Args:
            user: User instance
            user_ids: Optional list of user IDs for household scope

        Returns:
            List of years in descending order
        """
        return self.repo.get_transaction_years(user, user_ids=user_ids)

    def _to_float(self, value: Decimal) -> float:
        """Convert Decimal to float, rounded to 2 decimal places."""
        if value is None:
            return 0.0
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(rounded)
