"""Service layer for Expense business logic."""

import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal


class ExpenseService:
    """Service for managing Expense business logic - no ORM calls."""

    def __init__(self, expense_repo, account_repo, category_repo):
        """
        Initialize service with repository dependencies.

        Args:
            expense_repo: ExpenseRepository instance
            account_repo: AccountRepository or CardAccountRepository instance
            category_repo: CategoryRepository instance
        """
        self.expense_repo = expense_repo
        self.account_repo = account_repo
        self.category_repo = category_repo

    def get_user_expenses_formatted(
        self,
        user,
        limit: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        Get user expenses with formatted data for API response.

        Business logic: Formats expense data for table display.

        Args:
            user: User instance
            limit: Optional limit on number of entries
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with columns and rows for table display
        """
        entries = self.expense_repo.get_user_expenses_annotated(
            user, start_date, end_date
        )

        if limit is not None:
            entries = entries[:limit]

        return {
            "columns": [
                {"field": "id", "title": "ID"},
                {"field": "date", "title": "Date"},
                {"field": "description", "title": "Description"},
                {"field": "amount", "title": "Amount"},
                {"field": "Account", "title": "Account"},
                {"field": "Category", "title": "Category"},
            ],
            "rows": list(entries),
        }

    def create_expense(
        self,
        user,
        account_id: int,
        description: str,
        date_value: date,
        amount: Decimal,
        category_id: int | None = None,
        details: dict | None = None,
    ) -> tuple[object | None, str | None]:
        """
        Create a new expense with validation.

        Business logic: Validates account and category ownership before creation.

        Args:
            user: User instance
            account_id: CardAccount ID
            description: Expense description
            date_value: Expense date
            amount: Expense amount
            category_id: Optional Category ID
            details: Optional JSON details (OCR data, etc.)

        Returns:
            Tuple of (expense instance or None, error message or None)
        """
        # Business rule: Validate account ownership
        account = self.account_repo.get_by_id(account_id, user)
        if not account:
            return None, "Account not found for user"

        # Business rule: Validate category ownership (if provided)
        category = None
        if category_id is not None:
            category = self.category_repo.get_by_id(category_id, user)
            if not category:
                return None, "Category not found for user"

        # Create expense via repository
        expense = self.expense_repo.create_expense(
            user=user,
            account=account,
            category=category,
            description=description,
            date=date_value,
            amount=amount,
            details=details or {},
        )
        return expense, None

    def update_expense(
        self, user, expense_id: int, data: dict
    ) -> tuple[object | None, str | None]:
        """
        Update an existing expense with validation.

        Business logic: Validates ownership and allowed fields.

        Args:
            user: User instance
            expense_id: Expense ID to update
            data: Dictionary of fields to update

        Returns:
            Tuple of (updated expense or None, error message or None)
        """
        # Business rule: Check ownership
        expense = self.expense_repo.get_by_id(expense_id, user)
        if not expense:
            return None, "Expense not found"

        # Business rule: If updating account, validate ownership
        if "account_name" in data:
            account_id = data.get("account_name")
            if account_id:
                account = self.account_repo.get_by_id(account_id, user)
                if not account:
                    return None, "Account not found for user"
                data["account_name"] = account

        # Business rule: If updating category, validate ownership
        if "category" in data:
            category_id = data.get("category")
            if category_id:
                category = self.category_repo.get_by_id(category_id, user)
                if not category:
                    return None, "Category not found for user"
                data["category"] = category

        # Update via repository
        updated_expense = self.expense_repo.update_expense(expense, **data)
        return updated_expense, None

    def delete_expense(self, user, expense_id: int) -> tuple[bool, str | None]:
        """
        Delete an expense with ownership validation.

        Args:
            user: User instance
            expense_id: Expense ID to delete

        Returns:
            Tuple of (success boolean, error message or None)
        """
        # Business rule: Check ownership
        expense = self.expense_repo.get_by_id(expense_id, user)
        if not expense:
            return False, "Expense not found"

        # Delete via repository
        self.expense_repo.delete_expense(expense)
        return True, None

    def get_graph_data_by_day(self, user, days: int = 30) -> dict:
        """
        Generate line graph data by day for the last N days.

        Business logic: Aggregates expenses by day and formats for chart display.

        Args:
            user: User instance
            days: Number of days to include (default 30)

        Returns:
            Dictionary with labels and values for chart
        """
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Get expenses grouped by day
        daily_totals = self.expense_repo.get_expenses_grouped_by_day(
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

        Business logic: Aggregates expenses by month and formats for chart display.

        Args:
            user: User instance

        Returns:
            Dictionary with labels and values for chart
        """
        # Get earliest and latest expense dates
        expense_entries = self.expense_repo.get_user_expenses_limited(user)

        if not expense_entries:
            return {"labels": [], "values": []}

        # Find date range
        all_entries = list(expense_entries)
        if not all_entries:
            return {"labels": [], "values": []}

        earliest_date = min(entry.date for entry in all_entries)
        latest_date = max(entry.date for entry in all_entries)

        # Get expenses grouped by month
        monthly_totals = self.expense_repo.get_expenses_grouped_by_month(
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
        Get field choices for expense creation.

        Business logic: Formats account and category choices for dropdown.

        Args:
            user: User instance

        Returns:
            Dictionary with account and category choices
        """
        user_accounts = self.account_repo.get_user_accounts(user).values("id", "name")
        user_categories = self.category_repo.get_user_categories(user).values(
            "id", "name"
        )

        return {
            "account": [
                {"value": account["id"], "label": account["name"]}
                for account in user_accounts
            ],
            "category": [
                {"value": category["id"], "label": category["name"]}
                for category in user_categories
            ],
        }

    def get_existing_years(self, user) -> list[int]:
        """
        Get list of years where user has expenses.

        Business logic: Delegates to repository.

        Args:
            user: User instance

        Returns:
            Sorted list of years
        """
        return self.expense_repo.get_existing_years_for_user(user)
