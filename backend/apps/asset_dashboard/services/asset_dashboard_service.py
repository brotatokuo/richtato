"""Service layer for Asset Dashboard business logic."""

from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from utilities.tools import format_currency


class AssetDashboardService:
    """Service for Asset Dashboard calculations and aggregations - no ORM calls."""

    def __init__(self, asset_dashboard_repo):
        """
        Initialize service with repository dependency.

        Args:
            asset_dashboard_repo: AssetDashboardRepository instance
        """
        self.repo = asset_dashboard_repo

    def get_cash_flow_data(self, user, period: str = "6m") -> dict:
        """
        Generate cash flow data (income, expenses, net) by month.

        Business logic: Calculates date range based on period parameter.

        Args:
            user: User instance
            period: Period string ("6m", "1y", "all")

        Returns:
            Dictionary with labels and datasets for chart
        """
        # Business rule: Determine date range based on period
        end_date = date.today()

        if period == "6m":
            start_date = end_date - relativedelta(months=6)
        elif period == "1y":
            start_date = end_date - relativedelta(years=1)
        elif period == "all":
            # Get earliest date from income or expenses
            earliest_income = self.repo.get_earliest_income_date(user)
            earliest_expense = self.repo.get_earliest_expense_date(user)

            if earliest_income and earliest_expense:
                start_date = min(earliest_income, earliest_expense)
            elif earliest_income:
                start_date = earliest_income
            elif earliest_expense:
                start_date = earliest_expense
            else:
                start_date = end_date - relativedelta(months=6)  # Default fallback
        else:
            # Default to 6 months
            start_date = end_date - relativedelta(months=6)

        # Generate monthly labels and data
        (
            labels,
            income_data,
            expense_data,
            net_cash_flow,
        ) = self._calculate_monthly_cash_flow(user, start_date, end_date)

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Net Cash Flow",
                    "data": net_cash_flow,
                    "borderColor": "#98CC2C",
                    "backgroundColor": "rgba(152, 204, 44, 0.1)",
                    "fill": True,
                    "tension": 0.4,
                },
                {
                    "label": "Income",
                    "data": income_data,
                    "borderColor": "#4CAF50",
                    "backgroundColor": "transparent",
                    "borderDash": [5, 5],
                },
                {
                    "label": "Expenses",
                    "data": expense_data,
                    "borderColor": "#FF6B6B",
                    "backgroundColor": "transparent",
                    "borderDash": [5, 5],
                },
            ],
        }

    def get_income_expenses_data(
        self, user, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        """
        Generate monthly income vs expenses comparison for bar chart.

        Business logic: Calculates monthly totals for comparison.

        Args:
            user: User instance
            start_date: Optional start date (defaults to 6 months ago)
            end_date: Optional end date (defaults to today)

        Returns:
            Dictionary with labels and datasets for chart
        """
        # Business rule: Default date range
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - relativedelta(months=6)

        labels, income_data, expense_data, _ = self._calculate_monthly_cash_flow(
            user, start_date, end_date
        )

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Income",
                    "data": income_data,
                    "backgroundColor": "#98CC2C",
                    "borderRadius": 4,
                },
                {
                    "label": "Expenses",
                    "data": expense_data,
                    "backgroundColor": "#FF6B6B",
                    "borderRadius": 4,
                },
            ],
        }

    def get_savings_data(self, user) -> dict:
        """
        Generate savings accumulation data for the last 6 months.

        Business logic: Calculates running total of savings (income - expenses).

        Args:
            user: User instance

        Returns:
            Dictionary with labels and datasets for chart
        """
        end_date = date.today()
        start_date = end_date - relativedelta(months=6)

        labels = []
        total_savings = []
        monthly_savings = []
        running_total = 0

        current_date = start_date.replace(day=1)

        while current_date <= end_date:
            labels.append(current_date.strftime("%b"))

            month_end = current_date + relativedelta(months=1) - timedelta(days=1)

            # Get monthly income and expenses
            monthly_income = self.repo.get_income_sum_by_date_range(
                user, current_date, month_end
            )
            monthly_expense = self.repo.get_expense_sum_by_date_range(
                user, current_date, month_end
            )

            # Business rule: Savings = Income - Expenses
            monthly_saving = float(monthly_income - monthly_expense)
            running_total += monthly_saving

            monthly_savings.append(monthly_saving)
            total_savings.append(running_total)

            current_date += relativedelta(months=1)

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Total Savings",
                    "data": total_savings,
                    "borderColor": "#98CC2C",
                    "backgroundColor": "rgba(152, 204, 44, 0.1)",
                    "fill": True,
                    "tension": 0.4,
                },
                {
                    "label": "Monthly Savings",
                    "data": monthly_savings,
                    "type": "bar",
                    "backgroundColor": "#4CAF50",
                    "borderRadius": 4,
                },
            ],
        }

    def get_dashboard_metrics(self, user) -> dict:
        """
        Calculate key dashboard metrics.

        Business logic: Aggregates multiple metrics for dashboard cards.

        Args:
            user: User instance

        Returns:
            Dictionary with formatted metrics
        """
        # Calculate networth
        networth = self.repo.get_networth(user)

        # Calculate networth growth
        networth_growth = self._calculate_networth_growth(user)
        networth_growth_class = (
            "positive"
            if networth_growth.startswith("+")
            else "negative"
            if networth_growth.startswith("-")
            else ""
        )

        # Calculate cash flow for past 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        today = date.today()

        income_30_days = self.repo.get_income_sum_by_date_range(
            user, thirty_days_ago, today
        )
        expense_30_days = self.repo.get_expense_sum_by_date_range(
            user, thirty_days_ago, today
        )

        cash_flow_30_days = income_30_days - expense_30_days

        # Calculate savings rate
        if income_30_days > 0:
            savings_rate = round((cash_flow_30_days / income_30_days) * 100, 1)
        else:
            savings_rate = 0

        savings_rate_str = f"{savings_rate}%"
        savings_rate_context, savings_rate_class = self._calculate_savings_rate_context(
            savings_rate_str
        )

        return {
            "networth": format_currency(networth, 0),
            "networth_growth": networth_growth,
            "networth_growth_class": networth_growth_class,
            "expense_sum": format_currency(expense_30_days),
            "income_sum": format_currency(income_30_days),
            "savings_rate": savings_rate_str,
            "savings_rate_context": savings_rate_context,
            "savings_rate_class": savings_rate_class,
        }

    def _calculate_monthly_cash_flow(
        self, user, start_date: date, end_date: date
    ) -> tuple[list[str], list[float], list[float], list[float]]:
        """
        Calculate monthly income, expenses, and net cash flow.

        Business logic: Iterates through months and aggregates data.

        Returns:
            Tuple of (labels, income_data, expense_data, net_cash_flow)
        """
        labels = []
        income_data = []
        expense_data = []
        net_cash_flow = []

        current_date = start_date.replace(day=1)
        month_count = 0

        while current_date <= end_date:
            labels.append(current_date.strftime("%b"))

            month_start = start_date.replace(day=1) + relativedelta(months=month_count)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)

            # Get monthly totals via repository
            monthly_income = self.repo.get_income_sum_by_date_range(
                user, month_start, month_end
            )
            monthly_expense = self.repo.get_expense_sum_by_date_range(
                user, month_start, month_end
            )

            income_data.append(float(monthly_income))
            expense_data.append(float(monthly_expense))
            net_cash_flow.append(float(monthly_income - monthly_expense))

            current_date += relativedelta(months=1)
            month_count += 1

        return labels, income_data, expense_data, net_cash_flow

    def _calculate_networth_growth(self, user) -> str:
        """
        Calculate networth growth for the current month.

        Business logic: Compares current networth to previous month.

        Returns:
            Formatted string like "+5.2% this month"
        """
        try:
            current_date = date.today()
            current_month_start = current_date.replace(day=1)
            previous_month_end = current_month_start - timedelta(days=1)

            # Get current networth
            current_networth = self.repo.get_networth(user)

            # Get previous month's networth
            previous_networth = Decimal("0")
            accounts = self.repo.get_user_accounts(user)

            for account in accounts:
                balance = self.repo.get_account_balance_before_date(
                    account, current_month_start
                )
                previous_networth += balance

            # Business rule: Calculate growth percentage
            if previous_networth > 0:
                growth_percentage = (
                    (current_networth - previous_networth) / previous_networth
                ) * 100
                growth_percentage = round(growth_percentage, 1)

                if growth_percentage >= 0:
                    return f"+{growth_percentage}% this month"
                else:
                    return f"{growth_percentage}% this month"
            else:
                return "New this month"

        except Exception:
            return "N/A"

    def _calculate_savings_rate_context(self, savings_rate: str) -> tuple[str, str]:
        """
        Calculate savings rate context text and CSS class.

        Business logic: Categorizes savings rate into ranges.

        Args:
            savings_rate: Savings rate string like "15%"

        Returns:
            Tuple of (context_text, css_class)
        """
        try:
            rate_value = float(savings_rate.replace("%", ""))

            if rate_value < 10:
                return "Below average", "negative"
            elif 10 <= rate_value <= 20:
                return "Average", ""
            elif rate_value > 30:
                return "Above average", "positive"
            else:
                # Between 20-30%
                return "Good", "positive"

        except (ValueError, AttributeError):
            return "N/A", ""
