"""Data importer utility for CSV imports."""

import os

import colorama
import pandas as pd
from apps.account.models import Account, AccountTransaction
from apps.card.models import CardAccount
from apps.category.models import Category
from apps.expense.models import Expense
from apps.income.models import Income


class DataImporter:
    """Utility class for importing data from CSV files."""

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
        self._generate_csv_template("Card.csv", ["name"])
        self._generate_csv_template(
            "Category.csv", ["name", "keywords", "budget", "type", "color"]
        )
        self._generate_csv_template(
            "Expense.csv",
            ["description", "date", "amount", "account_name", "category_name"],
        )
        self._generate_csv_template(
            "Income.csv", ["description", "date", "amount", "account_name"]
        )
        self._generate_csv_template("Account.csv", ["type", "name"])
        self._generate_csv_template(
            "AccountTransactions.csv", ["amount", "date", "account_name"]
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

    def import_cards_from_csv(self):
        """Import card accounts from Card.csv."""
        cards_df = pd.read_csv(os.path.join(self.path, "Card.csv"))
        print(cards_df.head())
        for index, row in cards_df.iterrows():
            card = CardAccount(user=self.user, name=row["name"])
            card.save()

    def import_categories_from_csv(self):
        """Import categories from Category.csv."""
        categories_df = pd.read_csv(os.path.join(self.path, "Category.csv"))
        print(categories_df.head())
        for index, row in categories_df.iterrows():
            category_type = row["type"].lower().replace(" ", "").strip()
            assert category_type in [
                "essential",
                "nonessential",
            ], "Category type must be either essential or nonessential"
            category = Category(
                user=self.user,
                name=row["name"],
                keywords=row["keywords"],
                budget=row["budget"],
                type=category_type,
                color=row["color"],
            )
            category.save()

    def import_expenses_from_csv(self):
        """Import expenses from Expense.csv."""
        expenses_df = pd.read_csv(os.path.join(self.path, "Expense.csv"))
        print(expenses_df.head())
        for index, row in expenses_df.iterrows():
            account = CardAccount.objects.get(user=self.user, name=row["account_name"])
            category = Category.objects.get(user=self.user, name=row["category_name"])
            try:
                expense = Expense(
                    user=self.user,
                    description=row["description"],
                    date=row["date"],
                    amount=row["amount"],
                    account_name=account,
                    category=category,
                )
                expense.save()
            except Exception as e:
                print(
                    colorama.Fore.RED
                    + f"Error importing {row}"
                    + colorama.Style.RESET_ALL
                )
                print(e)
                print(f"Error importing {row}")

    def import_accounts_from_csv(self):
        """Import accounts from Account.csv."""
        accounts_df = pd.read_csv(os.path.join(self.path, "Account.csv"))
        print(accounts_df.head())
        for index, row in accounts_df.iterrows():
            account = Account(
                user=self.user,
                type=row["type"],
                name=row["name"],
            )
            account.save()

    def import_account_transactions_from_csv(self):
        """Import account transactions from AccountTransactions.csv."""
        transactions_df = pd.read_csv(
            os.path.join(self.path, "AccountTransactions.csv")
        )
        print(transactions_df.head())
        for index, row in transactions_df.iterrows():
            account = Account.objects.get(user=self.user, name=row["account_name"])
            transaction = AccountTransaction(
                account=account, amount=row["amount"], date=row["date"]
            )
            transaction.save()

    def import_incomes_from_csv(self):
        """Import incomes from Income.csv."""
        incomes_df = pd.read_csv(os.path.join(self.path, "Income.csv"))
        print(incomes_df.head())
        for index, row in incomes_df.iterrows():
            account = Account.objects.get(user=self.user, name=row["account_name"])
            income = Income(
                user=self.user,
                description=row["description"],
                date=row["date"],
                amount=row["amount"],
                account_name=account,
            )
            income.save()
