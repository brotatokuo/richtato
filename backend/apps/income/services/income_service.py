"""Service layer for Income business logic."""

import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal


class IncomeService:
    """Service for managing Income business logic - no ORM calls."""

    def __init__(self, income_repo, account_repo):
        """
        Initialize service with repository dependencies.

        Args:
            income_repo: IncomeRepository instance
            account_repo: AccountRepository instance
        """
        self.income_repo = income_repo
        self.account_repo = account_repo

    def get_user_income_formatted(
        self,
        user,
        limit: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        Get user income entries with formatted data for API response.

        Business logic: Formats income data for table display.

        Args:
            user: User instance
            limit: Optional limit on number of entries
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with columns and rows for table display
        """
        entries = self.income_repo.get_user_income_annotated(user, start_date, end_date)

        if limit is not None:
            entries = entries[:limit]

        return {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "Account", "title": "Account"},
                {"field": "description", "title": "Description"},
                {"field": "amount", "title": "Amount"},
            ],
            "rows": list(entries),
        }

    def create_income(
        self, user, account_id: int, description: str, date_value: date, amount: Decimal
    ) -> tuple[object | None, str | None]:
        """
        Create a new income entry with validation.

        Business logic: Validates account ownership before creation.

        Args:
            user: User instance
            account_id: Account ID
            description: Income description
            date_value: Income date
            amount: Income amount

        Returns:
            Tuple of (income instance or None, error message or None)
        """
        # Business rule: Validate account ownership
        account = self.account_repo.get_by_id(account_id, user)
        if not account:
            return None, "Account not found for user"

        # Create income via repository
        income = self.income_repo.create_income(
            user=user,
            account_name=account,
            description=description,
            date=date_value,
            amount=amount,
        )
        return income, None

    def update_income(
        self, user, income_id: int, data: dict
    ) -> tuple[object | None, str | None]:
        """
        Update an existing income entry with validation.

        Business logic: Validates ownership and allowed fields.

        Args:
            user: User instance
            income_id: Income ID to update
            data: Dictionary of fields to update

        Returns:
            Tuple of (updated income or None, error message or None)
        """
        # Business rule: Check ownership
        income = self.income_repo.get_by_id(income_id, user)
        if not income:
            return None, "Income not found"

        # Business rule: If updating account, validate ownership
        if "account_name" in data or "Account" in data:
            account_id = data.get("account_name") or data.get("Account")
            if account_id:
                account = self.account_repo.get_by_id(account_id, user)
                if not account:
                    return None, "Account not found for user"
                data["account_name"] = account

        # Update via repository
        updated_income = self.income_repo.update_income(income, **data)
        return updated_income, None

    def delete_income(self, user, income_id: int) -> tuple[bool, str | None]:
        """
        Delete an income entry with ownership validation.

        Business logic: Validates ownership before deletion.

        Args:
            user: User instance
            income_id: Income ID to delete

        Returns:
            Tuple of (success boolean, error message or None)
        """
        # Business rule: Check ownership
        income = self.income_repo.get_by_id(income_id, user)
        if not income:
            return False, "Income not found"

        # Delete via repository
        self.income_repo.delete_income(income)
        return True, None

    def get_graph_data_by_day(self, user, days: int = 30) -> dict:
        """
        Generate line graph data by day for the last N days.

        Business logic: Aggregates income by day and formats for chart display.

        Args:
            user: User instance
            days: Number of days to include (default 30)

        Returns:
            Dictionary with labels and values for chart
        """
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Get income grouped by day
        daily_totals = self.income_repo.get_income_grouped_by_day(
            user, start_date, end_date
        )

        # Generate labels and values for all days in range
        labels = []
        values = []

        current_date = start_date
        while current_date <= end_date:
            labels.append(current_date.strftime("%b %d"))
            values.append(float(daily_totals.get(current_date, Decimal("0"))))
            current_date += timedelta(days=1)

        return {"labels": labels, "values": values}

    def get_graph_data_by_month(self, user) -> dict:
        """
        Generate line graph data by month for all time.

        Business logic: Aggregates income by month and formats for chart display.

        Args:
            user: User instance

        Returns:
            Dictionary with labels and values for chart
        """
        # Get earliest and latest income dates
        income_entries = self.income_repo.get_user_income_limited(user)

        if not income_entries:
            return {"labels": [], "values": []}

        # Find date range
        all_entries = list(income_entries)
        if not all_entries:
            return {"labels": [], "values": []}

        earliest_date = min(entry.date for entry in all_entries)
        latest_date = max(entry.date for entry in all_entries)

        # Get income grouped by month
        monthly_totals = self.income_repo.get_income_grouped_by_month(
            user, earliest_date, latest_date
        )

        # Generate labels and values for all months in range
        labels = []
        values = []

        current_year = earliest_date.year
        current_month = earliest_date.month

        while (current_year, current_month) <= (latest_date.year, latest_date.month):
            # Create label (e.g., "Jan 2024")
            month_name = calendar.month_abbr[current_month]
            labels.append(f"{month_name} {current_year}")

            # Get value for this month
            month_key = (current_year, current_month)
            values.append(float(monthly_totals.get(month_key, Decimal("0"))))

            # Move to next month
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

        return {"labels": labels, "values": values}

    def get_field_choices(self, user) -> dict:
        """
        Get field choices for income creation.

        Business logic: Formats account choices for dropdown.

        Args:
            user: User instance

        Returns:
            Dictionary with account choices
        """
        user_accounts = self.account_repo.get_user_accounts(user).values("id", "name")
        return {
            "account": [
                {"value": account["id"], "label": account["name"]}
                for account in user_accounts
            ],
        }
