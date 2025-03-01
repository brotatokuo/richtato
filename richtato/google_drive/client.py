import os
import re
from datetime import datetime

import colorama
import gspread
import pandas as pd
from django.http import FileResponse, Http404
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe

from richtato.apps.account.models import Account, AccountTransaction
from richtato.apps.expense.models import Expense
from richtato.apps.income.models import Income
from richtato.apps.richtato_user.models import CardAccount, Category, User


class GoogleSheetsClient:
    def __init__(self, user: User):
        self.user = user

        print("User: ", user)
        print("User google sheets link: ", user.google_sheets_link)

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        parent_path = os.path.dirname(os.path.abspath(__file__))
        creds = Credentials.from_service_account_file(
            ".sheets_creds.json", scopes=scopes
        )

        self.client = gspread.authorize(creds)
        self.sheet_id = re.search(
            r"/d/([a-zA-Z0-9-_]+)", user.google_sheets_link
        ).group(1)
        self.sheets_dict = {
            "cards": ["id", "name"],
            "categories": [
                "id",
                "name",
                "keywords",
                "budget",
                "type",
                "color",
            ],
            "income": [
                "id",
                "description",
                "date",
                "amount",
                "account_name",
                "account_name_id",
            ],
            "expense": [
                "id",
                "description",
                "date",
                "amount",
                "account_name_id",
                "category_id",
            ],
            "account": ["id", "type", "name", "latest_balance", "latest_balance_date"],
            "account_transactions": ["id", "amount", "date", "account_id"],
        }

        self.workbook = self.client.open_by_key(self.sheet_id)

    def generate_templates(self):
        worksheets = self.workbook.worksheets()
        worksheet_names = [sheet.title for sheet in worksheets]
        print("Worksheet names: ", worksheet_names)
        for sheet in self.sheets_dict.keys():
            print("Sheet: ", sheet)
            if sheet not in worksheet_names:
                self.workbook.add_worksheet(title=sheet, rows="100", cols="20")
                data = self.workbook.worksheet(sheet)
                data.clear()
                data.insert_row(self.sheets_dict[sheet], 1)

    def _delete_sheets(self):
        for sheet in self.sheets_dict.keys():
            if sheet in self.sheets_dict.keys():
                self.workbook.del_worksheet(self.workbook.worksheet(sheet))


class ImporterClient(GoogleSheetsClient):
    def import_data(self):
        self.import_cards()
        self.import_categories()
        self.import_accounts()
        self.import_account_transactions()
        self.import_expenses()
        self.import_incomes()

    def import_cards(self):
        print("Importing cards")
        try:
            data = self.workbook.worksheet("cards")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            self.cards_dict = {}
            for _, row in df.iterrows():
                card = CardAccount(user=self.user, name=row["name"])
                card.save()

                id = row["id"]
                self.cards_dict[id] = card

            print("Successfully imported cards")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def import_categories(self):
        print("Importing categories")
        try:
            data = self.workbook.worksheet("categories")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            self.categories_dict = {}
            for _, row in df.iterrows():
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

                id = row["id"]
                self.categories_dict[id] = category

            print("Successfully imported categories")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def import_accounts(self):
        print("Importing accounts")
        try:
            data = self.workbook.worksheet("account")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            self.accounts_dict = {}
            for _, row in df.iterrows():
                account = Account(
                    user=self.user,
                    type=row["type"],
                    name=row["name"],
                    latest_balance=row["latest_balance"],
                    latest_balance_date=row["latest_balance_date"],
                )
                account.save()

                id = row["id"]
                self.accounts_dict[id] = account

            print("Successfully imported accounts")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def import_account_transactions(self):
        print("Importing account transactions")
        try:
            data = self.workbook.worksheet("account_transactions")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            for _, row in df.iterrows():
                if "account_name" in df.columns and "account_id" not in df.columns:
                    account = Account.objects.get(
                        user=self.user, name=row["account_name"]
                    )
                elif "account_id" in df.columns and "account_name" not in df.columns:
                    account = self.accounts_dict[row["account_id"]]
                else:
                    raise Exception(
                        "Account name or account id must be provided for account transactions"
                    )

                transaction = AccountTransaction(
                    account=account, amount=row["amount"], date=row["date"]
                )
                transaction.save()

                print("Successfully imported account transactions")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def import_expenses(self):
        print("Importing expenses")
        try:
            data = self.workbook.worksheet("expense")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            for _, row in df.iterrows():
                if "account_name_id" in df.columns:
                    account = self.cards_dict[row["account_name_id"]]
                elif "account_name" in df.columns:
                    account = CardAccount.objects.get(
                        user=self.user, name=row["account_name"]
                    )
                else:
                    raise Exception(
                        "account_name or account_name_id must be provided for expenses"
                    )

                if "category_name" in df.columns and "category_id" not in df.columns:
                    category = Category.objects.get(
                        user=self.user, name=row["category_name"]
                    )
                elif "category_id" in df.columns and "category_name" not in df.columns:
                    category = self.categories_dict[row["category_id"]]
                else:
                    raise Exception(
                        "Category name or category id must be provided for expenses"
                    )

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

                except Exception:
                    print(
                        colorama.Fore.RED
                        + f"Error importing {row}"
                        + colorama.Style.RESET_ALL
                    )
                    print(f"Error importing {row}")

            print("Successfully imported expenses")

        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def import_incomes(self):
        print("Importing incomes")
        try:
            data = self.workbook.worksheet("income")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            for _, row in df.iterrows():
                if "account_name_id" in df.columns:
                    account = self.accounts_dict[row["account_name_id"]]
                elif "account_name" in df.columns:
                    account = Account.objects.get(
                        user=self.user, name=row["account_name"]
                    )
                else:
                    raise Exception(
                        "account_name or account_name_id must be provided for incomes"
                    )

                income = Income(
                    user=self.user,
                    description=row["description"],
                    date=row["date"],
                    amount=row["amount"],
                    account_name=account,
                )
                income.save()

            print("Successfully imported incomes")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)


class GoogleExporterClient(GoogleSheetsClient):
    def export_data(self):
        self.export_cards()
        self.export_categories()
        self.export_accounts()
        self.export_account_transactions()
        self.export_expenses()
        self.export_incomes()

    def export_cards(self):
        print("Exporting cards")
        try:
            cards = CardAccount.objects.filter(user=self.user)
            data = [[i + 1, card.name] for i, card in enumerate(cards)]
            # Write the 'cards' data to google sheets
            df = pd.DataFrame(data, columns=self.sheets_dict["cards"])
            self.workbook.worksheet("cards").clear()
            set_with_dataframe(self.workbook.worksheet("cards"), df)

            print("Successfully exported cards")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_categories(self):
        print("Exporting categories")
        try:
            categories = Category.objects.filter(user=self.user)
            data = [
                [
                    i + 1,
                    category.name,
                    category.keywords,
                    category.budget,
                    category.type,
                    category.color,
                ]
                for i, category in enumerate(categories)
            ]
            # Write the 'categories' data to google sheets
            df = pd.DataFrame(data, columns=self.sheets_dict["categories"])
            self.workbook.worksheet("categories").clear()
            set_with_dataframe(self.workbook.worksheet("categories"), df)

            print("Successfully exported categories")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_accounts(self):
        print("Exporting accounts")
        try:
            accounts = Account.objects.filter(user=self.user)
            data = [
                [
                    i + 1,
                    account.type,
                    account.name,
                    account.latest_balance,
                    account.latest_balance_date,
                ]
                for i, account in enumerate(accounts)
            ]
            # Write the 'accounts' data to google sheets
            df = pd.DataFrame(data, columns=self.sheets_dict["account"])
            self.workbook.worksheet("account").clear()
            set_with_dataframe(self.workbook.worksheet("account"), df)

            print("Successfully exported accounts")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_account_transactions(self):
        print("Exporting account transactions")
        try:
            transactions = AccountTransaction.objects.filter(account__user=self.user)
            data = [
                [i + 1, transaction.amount, transaction.date, transaction.account.id]
                for i, transaction in enumerate(transactions)
            ]
            # Write the 'account_transactions' data to google sheets
            df = pd.DataFrame(data, columns=self.sheets_dict["account_transactions"])
            self.workbook.worksheet("account_transactions").clear()
            set_with_dataframe(self.workbook.worksheet("account_transactions"), df)

            print("Successfully exported account transactions")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_expenses(self):
        print("Exporting expenses")
        try:
            expenses = Expense.objects.filter(user=self.user)
            data = [
                [
                    i + 1,
                    expense.description,
                    expense.date,
                    expense.amount,
                    expense.account_name.id,
                    expense.category.id,
                ]
                for i, expense in enumerate(expenses)
            ]
            # Write the 'expenses' data to google sheets
            df = pd.DataFrame(data, columns=self.sheets_dict["expense"])
            self.workbook.worksheet("expense").clear()
            set_with_dataframe(self.workbook.worksheet("expense"), df)

            print("Successfully exported expenses")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_incomes(self):
        print("Exporting incomes")
        try:
            incomes = Income.objects.filter(user=self.user)
            data = [
                [
                    i + 1,
                    income.description,
                    income.date,
                    income.amount,
                    income.account_name,
                    income.account_name.id,
                ]
                for i, income in enumerate(incomes)
            ]
            # Write the 'incomes' data to google sheets
            df = pd.DataFrame(data, columns=self.sheets_dict["income"])
            self.workbook.worksheet("income").clear()
            set_with_dataframe(self.workbook.worksheet("income"), df)

            print("Successfully exported incomes")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)


class ExporterClient:
    def __init__(self, user: User):
        self.user = user
        self.sheets_dict = {
            "cards": ["id", "name"],
            "categories": [
                "id",
                "name",
                "keywords",
                "budget",
                "type",
                "color",
            ],
            "income": [
                "id",
                "description",
                "date",
                "amount",
                "account_name",
                "account_name_id",
            ],
            "expense": [
                "id",
                "description",
                "date",
                "amount",
                "account_name_id",
                "category_id",
            ],
            "account": ["id", "type", "name", "latest_balance", "latest_balance_date"],
            "account_transactions": ["id", "amount", "date", "account_id"],
        }
        self.path = os.path.expanduser("~")
        self.file_path = f"{self.path}/richtato_export.xlsx"

    def export_data(self):
        with pd.ExcelWriter(self.file_path) as writer:
            self.export_cards(writer)
            self.export_categories(writer)
            self.export_accounts(writer)
            self.export_account_transactions(writer)
            self.export_expenses(writer)
            self.export_incomes(writer)

        return self.download_excel()

    def download_excel(self):
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            print("username: ", self.user.username)
            file_name = f"richtato_export_{date_str}.xlsx"
            print("File name: ", file_name)
            return FileResponse(
                open(self.file_path, "rb"), as_attachment=True, filename=file_name
            )
        except FileNotFoundError:
            raise Http404("File not found.")

    def export_cards(self, writer):
        print("Exporting cards")
        try:
            cards = CardAccount.objects.filter(user=self.user)
            data = [[i + 1, card.name] for i, card in enumerate(cards)]

            # Write the 'cards' data to the sheet
            df = pd.DataFrame(data, columns=self.sheets_dict["cards"])
            df.to_excel(writer, sheet_name="cards", index=False, header=True)

            print("Successfully exported cards")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_categories(self, writer):
        print("Exporting categories")
        try:
            categories = Category.objects.filter(user=self.user)
            data = [
                [
                    i + 1,
                    category.name,
                    category.keywords,
                    category.budget,
                    category.type,
                    category.color,
                ]
                for i, category in enumerate(categories)
            ]

            # Write the 'categories' data to the sheet
            df = pd.DataFrame(data, columns=self.sheets_dict["categories"])
            df.to_excel(writer, sheet_name="categories", index=False, header=True)

            print("Successfully exported categories")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_accounts(self, writer):
        print("Exporting accounts")
        try:
            accounts = Account.objects.filter(user=self.user)
            data = [
                [
                    i + 1,
                    account.type,
                    account.name,
                    account.latest_balance,
                    self._date_to_string(account.latest_balance_date),
                ]
                for i, account in enumerate(accounts)
            ]

            # Write the 'accounts' data to the sheet
            df = pd.DataFrame(data, columns=self.sheets_dict["account"])
            df.to_excel(writer, sheet_name="account", index=False, header=True)

            print("Successfully exported accounts")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_account_transactions(self, writer):
        print("Exporting account transactions")
        try:
            transactions = AccountTransaction.objects.filter(account__user=self.user)
            data = [
                [
                    i + 1,
                    transaction.amount,
                    self._date_to_string(transaction.date),
                    transaction.account.id,
                ]
                for i, transaction in enumerate(transactions)
            ]

            # Write the 'account_transactions' data to the sheet
            df = pd.DataFrame(data, columns=self.sheets_dict["account_transactions"])
            df.to_excel(
                writer, sheet_name="account_transactions", index=False, header=True
            )

            print("Successfully exported account transactions")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_expenses(self, writer):
        print("Exporting expenses")
        try:
            expenses = Expense.objects.filter(user=self.user)
            data = [
                [
                    i + 1,
                    expense.description,
                    self._date_to_string(expense.date),
                    expense.amount,
                    expense.account_name.id,
                    expense.category.id,
                ]
                for i, expense in enumerate(expenses)
            ]

            # Write the 'expenses' data to the sheet
            df = pd.DataFrame(data, columns=self.sheets_dict["expense"])
            df.to_excel(writer, sheet_name="expense", index=False, header=True)

            print("Successfully exported expenses")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def export_incomes(self, writer):
        print("Exporting incomes")
        try:
            incomes = Income.objects.filter(user=self.user)
            data = [
                [
                    i + 1,
                    income.description,
                    self._date_to_string(income.date),
                    income.amount,
                    income.account_name,
                    income.account_name.id,
                ]
                for i, income in enumerate(incomes)
            ]

            # Write the 'incomes' data to the sheet
            df = pd.DataFrame(data, columns=self.sheets_dict["income"])
            df.to_excel(writer, sheet_name="income", index=False, header=True)

            print("Successfully exported incomes")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)

    def _date_to_string(self, date):
        return date.strftime("%Y-%m-%d")
