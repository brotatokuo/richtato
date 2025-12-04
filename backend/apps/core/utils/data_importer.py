"""Data importer utility for CSV imports."""

import os
from decimal import Decimal

import colorama
import pandas as pd

from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.transaction.models import Transaction, TransactionCategory


class DataImporter:
    """Utility class for importing data from CSV files.

    Uses the unified Transaction model for all transactions.
    """

    def __init__(self, user, path):
        """
        Initialize the DataImporter object.

        Args:
            user: User instance
            path: Path to the folder containing the CSV files to be imported
        """
        self.user = user
        self.path = path

    def __str__(self):
        return f"Data Importer for {self.user} at {self.path}"

    def generate_csv_templates(self):
        """Generate blank CSV template files for all import types."""
        self._generate_csv_template(
            "Account.csv", ["name", "account_type", "institution", "last4"]
        )
        self._generate_csv_template(
            "Category.csv", ["name", "slug", "is_income", "is_expense", "icon", "color"]
        )
        self._generate_csv_template(
            "Transaction.csv",
            [
                "description",
                "date",
                "amount",
                "transaction_type",
                "account_name",
                "category_slug",
            ],
        )

    def _generate_csv_template(self, name, necessary_columns):
        """
        Generate a blank CSV file with the necessary columns.

        Args:
            name: Filename for the CSV template
            necessary_columns: List of column names
        """
        df = pd.DataFrame(columns=necessary_columns)
        df.to_csv(os.path.join(self.path, name), index=False)

    def import_accounts_from_csv(self):
        """Import financial accounts from Account.csv."""
        accounts_df = pd.read_csv(os.path.join(self.path, "Account.csv"))
        print(accounts_df.head())
        for index, row in accounts_df.iterrows():
            # Get or create institution if provided
            institution = None
            if pd.notna(row.get("institution")) and row["institution"]:
                institution, _ = FinancialInstitution.objects.get_or_create(
                    name=row["institution"],
                    defaults={"slug": row["institution"].lower().replace(" ", "-")},
                )

            FinancialAccount.objects.create(
                user=self.user,
                name=row["name"],
                account_type=row.get("account_type", "checking"),
                institution=institution,
                account_number_last4=row.get("last4", ""),
            )

    def import_categories_from_csv(self):
        """Import transaction categories from Category.csv."""
        categories_df = pd.read_csv(os.path.join(self.path, "Category.csv"))
        print(categories_df.head())
        for index, row in categories_df.iterrows():
            TransactionCategory.objects.create(
                user=self.user,
                name=row["name"],
                slug=row["slug"],
                is_income=row.get("is_income", False),
                is_expense=row.get("is_expense", True),
                icon=row.get("icon", ""),
                color=row.get("color", ""),
            )

    def import_transactions_from_csv(self):
        """Import transactions from Transaction.csv."""
        transactions_df = pd.read_csv(os.path.join(self.path, "Transaction.csv"))
        print(transactions_df.head())
        for index, row in transactions_df.iterrows():
            try:
                # Get the account
                account = FinancialAccount.objects.get(
                    user=self.user, name=row["account_name"]
                )

                # Get the category if provided
                category = None
                if pd.notna(row.get("category_slug")) and row["category_slug"]:
                    try:
                        category = TransactionCategory.objects.get(
                            user=self.user, slug=row["category_slug"]
                        )
                    except TransactionCategory.DoesNotExist:
                        # Try global categories
                        category = TransactionCategory.objects.filter(
                            user__isnull=True, slug=row["category_slug"]
                        ).first()

                # Determine transaction type
                transaction_type = row.get("transaction_type", "debit")
                if transaction_type not in ["debit", "credit"]:
                    # Infer from amount if not specified
                    amount = Decimal(str(row["amount"]))
                    transaction_type = "credit" if amount > 0 else "debit"

                Transaction.objects.create(
                    user=self.user,
                    account=account,
                    description=row["description"],
                    date=row["date"],
                    amount=abs(Decimal(str(row["amount"]))),
                    transaction_type=transaction_type,
                    category=category,
                    sync_source="csv",
                )
            except Exception as e:
                print(
                    colorama.Fore.RED
                    + f"Error importing {row}"
                    + colorama.Style.RESET_ALL
                )
                print(e)
                print(f"Error importing {row}")

    # Legacy import methods for backward compatibility
    # These can be removed after full migration

    def import_expenses_from_csv(self):
        """Import expenses from Expense.csv (legacy format)."""
        self.import_transactions_from_csv()

    def import_incomes_from_csv(self):
        """Import incomes from Income.csv (legacy format)."""
        self.import_transactions_from_csv()
