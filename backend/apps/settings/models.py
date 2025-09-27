import os

import colorama
import pandas as pd

from apps.account.models import Account, AccountTransaction
from apps.expense.models import Category, Expense
from apps.income.models import Income
from apps.richtato_user.models import CardAccount


# Create your models here.
class DataImporter:
    def __init__(self, user, path):
        """
        Initialize the DataImporter object
        user = user_id
        path = path to the folder containing the files to be imported
        """
        self.user = user
        self.path = path

    def __str__(self):
        return f"Data Importer for {self.user} at {self.path}"

    def generate_csv_templates(self):
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
        Generate a blank csv file with the necessary columns
        """
        df = pd.DataFrame(columns=necessary_columns)
        df.to_csv(os.path.join(self.path, name), index=False)

    def import_from_csv(self):
        # self.import_cards_from_csv()
        # print(colorama.Fore.GREEN + "Cards imported successfully" + colorama.Style.RESET_ALL)
        # self.import_categories_from_csv()
        # print(colorama.Fore.GREEN + "Categories imported successfully"+ colorama.Style.RESET_ALL)
        # self.import_expenses_from_csv()
        # print(colorama.Fore.GREEN + "Expenses imported successfully"+ colorama.Style.RESET_ALL)

        # self.import_accounts_from_csv()
        # print(colorama.Fore.GREEN + "Accounts imported successfully"+ colorama.Style.RESET_ALL)
        # self.import_account_transactions_from_csv()
        # print(colorama.Fore.GREEN + "Accounts Transactions imported successfully"+ colorama.Style.RESET_ALL)

        self.import_incomes_from_csv()
        print(
            colorama.Fore.GREEN
            + "Incomes imported successfully"
            + colorama.Style.RESET_ALL
        )

    def import_cards_from_csv(self):
        cards_df = pd.read_csv(os.path.join(self.path, "Card.csv"))
        print(cards_df.head())
        for index, row in cards_df.iterrows():
            card = CardAccount(user=self.user, name=row["name"])
            card.save()

    def import_categories_from_csv(self):
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
            income.save()
            income.save()
