"""Service layer for Expense import business logic."""

import pandas as pd
from loguru import logger


class ExpenseImportService:
    """Service for importing expenses from external sources - no ORM calls."""

    def __init__(self, expense_repo, account_repo, category_repo):
        """
        Initialize service with repository dependencies.

        Args:
            expense_repo: ExpenseRepository instance
            account_repo: CardAccountRepository instance
            category_repo: CategoryRepository instance
        """
        self.expense_repo = expense_repo
        self.account_repo = account_repo
        self.category_repo = category_repo

    def import_from_dataframe(
        self, df: pd.DataFrame, user
    ) -> tuple[int, int, list[str]]:
        """
        Import expenses from a pandas DataFrame.

        Business logic:
        - Validates each row
        - Maps card names to account IDs
        - Maps category names to category IDs (or creates "Unknown")
        - Creates expense entries

        Args:
            df: DataFrame with columns: Card, Category, Amount, Date, Description
            user: User instance

        Returns:
            Tuple of (success_count, error_count, error_messages)
        """
        success_count = 0
        error_count = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                # Business rule: Find account by name
                account = self._get_account_by_name(user, row["Card"])
                if not account:
                    error_msg = f"Row {idx}: Account '{row['Card']}' not found for user"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    error_count += 1
                    continue

                # Business rule: Find or create category
                category = self._get_or_create_category(user, row["Category"])
                if not category:
                    error_msg = f"Row {idx}: Could not resolve category"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    error_count += 1
                    continue

                # Create expense via repository
                self.expense_repo.create_expense(
                    user=user,
                    account=account,
                    category=category,
                    amount=row["Amount"],
                    date=row["Date"],
                    description=row["Description"],
                )
                success_count += 1

            except Exception as e:
                error_msg = f"Row {idx}: {str(e)}"
                logger.error(f"Error processing row: {e}")
                errors.append(error_msg)
                error_count += 1

        return success_count, error_count, errors

    def _get_account_by_name(self, user, account_name: str):
        """
        Get account by name for the user.

        Business logic: Query account by name with user filter.

        Args:
            user: User instance
            account_name: Name of the account

        Returns:
            Account instance or None
        """
        accounts = self.account_repo.get_user_accounts(user)
        for account in accounts:
            if account.name == account_name:
                return account
        return None

    def _get_or_create_category(self, user, category_name: str):
        """
        Get or create category by name.

        Business logic:
        - Try to find exact match
        - If not found, create/get "Unknown" category as fallback

        Args:
            user: User instance
            category_name: Name of the category

        Returns:
            Category instance
        """
        # Try to find category by name
        categories = self.category_repo.get_user_categories(user)
        for category in categories:
            if category.name == category_name:
                return category

        # Fallback: get or create "Unknown" category
        for category in categories:
            if category.name == "Unknown":
                return category

        # If "Unknown" doesn't exist, we need to create it
        # This is a data access operation that should be in repository
        # For now, return None and let the caller handle it
        # In a full implementation, add a create_category method to CategoryRepository
        logger.warning(
            f"Category '{category_name}' not found and 'Unknown' doesn't exist for user"
        )
        return None

    def categorize_transaction(
        self, user, description: str, ai_service
    ) -> tuple[int | None, str | None]:
        """
        Categorize a transaction using AI.

        Business logic:
        - Use AI service to determine category
        - Find category by name (case-insensitive)
        - Fallback to "Unknown" category

        Args:
            user: User instance
            description: Transaction description
            ai_service: AI service instance with categorize_transaction method

        Returns:
            Tuple of (category_id or None, error message or None)
        """
        try:
            # Business rule: Use AI to categorize
            category_name = ai_service.categorize_transaction(user, description)
        except Exception as e:
            logger.exception(f"AI categorize failed, falling back to 'Unknown': {e}")
            category_name = "Unknown"

        # Business rule: Find category (case-insensitive)
        categories = self.category_repo.get_user_categories(user)

        # Try exact match
        for category in categories:
            if category.name == category_name:
                return category.id, None

        # Try case-insensitive match
        for category in categories:
            if category.name.lower() == category_name.lower():
                return category.id, None

        # Fallback to "Unknown"
        for category in categories:
            if category.name == "Unknown":
                return category.id, None

        return None, "No suitable category found (including 'Unknown')"
