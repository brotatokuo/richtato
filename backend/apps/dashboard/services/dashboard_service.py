"""Service layer for Dashboard business logic."""

from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from utilities.tools import format_currency


class DashboardService:
    """Service for Dashboard calculations and aggregations - no ORM calls."""

    def __init__(self, dashboard_repo):
        """
        Initialize service with repository dependency.

        Args:
            dashboard_repo: DashboardRepository instance
        """
        self.dashboard_repo = dashboard_repo

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
            earliest_income = self.dashboard_repo.get_earliest_income_date(user)
            earliest_expense = self.dashboard_repo.get_earliest_expense_date(user)

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
            monthly_income = self.dashboard_repo.get_income_sum_by_date_range(
                user, month_start, month_end
            )
            monthly_expense = self.dashboard_repo.get_expense_sum_by_date_range(
                user, month_start, month_end
            )

            income_data.append(float(monthly_income))
            expense_data.append(float(monthly_expense))
            net_cash_flow.append(float(monthly_income - monthly_expense))

            current_date += relativedelta(months=1)
            month_count += 1

        return labels, income_data, expense_data, net_cash_flow

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
        expenses = self.dashboard_repo.get_expenses_by_category(
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
            monthly_income = self.dashboard_repo.get_income_sum_by_date_range(
                user, current_date, month_end
            )
            monthly_expense = self.dashboard_repo.get_expense_sum_by_date_range(
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
        networth = self.dashboard_repo.get_networth(user)

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

        income_30_days = self.dashboard_repo.get_income_sum_by_date_range(
            user, thirty_days_ago, today
        )
        expense_30_days = self.dashboard_repo.get_expense_sum_by_date_range(
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

        # Calculate non-essential spending percentage
        nonessential_expense = self.dashboard_repo.get_nonessential_expense_sum(
            user, thirty_days_ago, today
        )
        nonessential_spending_pct = (
            round((nonessential_expense / expense_30_days) * 100, 1)
            if expense_30_days > 0
            else 0
        )

        # Calculate budget utilization
        budget_utilization = self._calculate_budget_utilization(
            user, thirty_days_ago, today
        )

        return {
            "networth": format_currency(networth, 0),
            "networth_growth": networth_growth,
            "networth_growth_class": networth_growth_class,
            "expense_sum": format_currency(expense_30_days),
            "income_sum": format_currency(income_30_days),
            "budget_utilization_30_days": budget_utilization,
            "savings_rate": savings_rate_str,
            "savings_rate_context": savings_rate_context,
            "savings_rate_class": savings_rate_class,
            "nonessential_spending_pct": nonessential_spending_pct,
        }

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
            current_networth = self.dashboard_repo.get_networth(user)

            # Get previous month's networth
            previous_networth = Decimal("0")
            accounts = self.dashboard_repo.get_user_accounts(user)

            for account in accounts:
                balance = self.dashboard_repo.get_account_balance_before_date(
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

    def _calculate_budget_utilization(
        self, user, start_date: date, end_date: date
    ) -> str:
        """
        Calculate average budget utilization percentage.

        Business logic: Averages utilization across all active budgets.

        Returns:
            Formatted string like "75%" or "N/A"
        """
        month_start = date.today().replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(
            days=1
        )

        budgets = self.dashboard_repo.get_active_budgets_for_date_range(
            user, month_start, month_end
        )

        utilizations = []
        for budget in budgets:
            cat_expense = self.dashboard_repo.get_expense_sum_by_date_range(
                user, start_date, end_date
            )
            if budget.amount > 0:
                utilization = (Decimal(cat_expense) / budget.amount) * Decimal(100)
                utilizations.append(float(utilization))

        if utilizations:
            avg_utilization = round(sum(utilizations) / len(utilizations), 1)
            return f"{avg_utilization}%"
        else:
            return "N/A"

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
        import calendar

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

    def get_expense_years(self, user) -> list[int]:
        """
        Get list of years where user has expenses.

        Business logic: Delegates to repository.

        Args:
            user: User instance

        Returns:
            List of years
        """
        return self.dashboard_repo.get_expense_years(user)
