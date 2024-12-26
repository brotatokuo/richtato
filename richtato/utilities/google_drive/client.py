import gspread
import pandas as pd
import os
import colorama
from apps.richtato_user.models import User, CardAccount, Category
from apps.expense.models import Expense
from apps.income.models import Income
from apps.account.models import Account, AccountTransaction

from google.oauth2.service_account import Credentials
from gspread_formatting import format_cell_range, CellFormat, TextFormat


class GoogleSheetsClient:

    def __init__(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        parent_path = os.path.dirname(os.path.abspath(__file__))
        print(parent_path)
        creds = Credentials.from_service_account_file(f"{parent_path}/credentials/credentials.json", scopes=scopes)
        self.client = gspread.authorize(creds)

class ExpenseClient(GoogleSheetsClient):
    def __init__(self):
        super().__init__()
        sheet_id = "1eWiI0nPGNITBAdbDqfV9CWf3d6eMcy1zVnS3teE8-tI"
        self.workbook = self.client.open_by_key(sheet_id)
        self.header = ["Date", "Card", "Description", "Category", "Amount"]
    
    def get_table(self):
        data = self.workbook.worksheet("Expenses")
        df = pd.DataFrame(data.get_all_records())
        return df

    def clear_table(self):
        data = self.workbook.worksheet("Expenses")
        data.clear()

    def add_header(self):
        data = self.workbook.worksheet("Expenses")
        data.insert_row(self.header, 1)
        cell_range = 'A1:E1'
        header_format = CellFormat(
            textFormat=TextFormat(bold=True)
        )
        format_cell_range(data, cell_range, header_format)

class ImporterClient(GoogleSheetsClient):
    def __init__(self, username):
        super().__init__()
        sheet_id = "101_Ov7waagUS_pplSgyzQ_eekttQ_l0mvlpragcCqcQ"
        self.sheets = ["cards", "categories", "income", "expense", "account"]
        self.workbook = self.client.open_by_key(sheet_id)
        self.user = User.objects.get(username=username)

    def generate_import_template(self):
        sheets_dict = {
            "cards": ["id", "name"],
            "categories": ["id", "name", "keywords", "budget", "type", "color",],
            "income": ["id", "description", "date", "amount", "account_name", "account_name_id"],
            "expense": ["id", "description", "date", "amount", "account_name_id", "category_id"],
            "account": ["id", "type", "name", "latest_balance", "latest_balance_date"],
            "account_transactions": ["id", "amount", "date", "account_id"]
        }

        worksheets = self.workbook.worksheets()
        worksheet_names = [sheet.title for sheet in worksheets]
        for sheet in self.sheets:
            if sheet not in worksheet_names:
                self.workbook.add_worksheet(title=sheet, rows="100", cols="20")
                data = self.workbook.worksheet(sheet)
                data.clear()
                data.insert_row(sheets_dict[sheet], 1)

    def _delete_sheets(self):
        for sheet in self.sheets:
            if sheet in self.sheets:
                self.workbook.del_worksheet(self.workbook.worksheet(sheet))

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

            self.cards_dict ={}
            for _, row in df.iterrows():
                card = CardAccount(
                    user=self.user,
                    name=row["name"]
                )
                card.save()

                id = row["id"]
                self.cards_dict[id] = card
            
            print("Successfully imported cards")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
            print(e)
            
    
    def import_categories(self):
        print("Importing categories")
        try:
            data = self.workbook.worksheet("categories")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            self.categories_dict = {}
            for _, row in df.iterrows():
                category_type = row["type"].lower().replace(" ", "").strip()
                assert category_type in ["essential", "nonessential"], "Category type must be either essential or nonessential"
                category = Category(
                user=self.user,
                name=row["name"],
                keywords=row["keywords"],
                budget=row["budget"],
                type=category_type,
                color=row["color"]
                )
                category.save()

            id = row["id"]
            self.categories_dict[id] = category

            print("Successfully imported categories")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
            print(e)

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
                )
                account.save()

                id = row["id"]
                self.accounts_dict[id] = account

            print("Successfully imported accounts")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
            print(e)

    def import_account_transactions(self):
        print("Importing account transactions")
        try:
            data = self.workbook.worksheet("account_transactions")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            for _, row in df.iterrows():
                if "account_name" in df.columns and "account_id" not in df.columns:
                    account = Account.objects.get(user=self.user, name=row["account_name"])
                elif "account_id" in df.columns and "account_name" not in df.columns:
                    account = self.accounts_dict[row["account_id"]]
                else:
                    raise Exception("Account name or account id must be provided")
                
                transaction = AccountTransaction(
                    account=account,
                    amount=row["amount"],
                    date=row["date"]
                )
                transaction.save()
    
                print("Successfully imported account transactions") 
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
            print(e)


    def import_expenses(self):
        print("Importing expenses")
        try:
            data = self.workbook.worksheet("expenses")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())
            
            for _, row in df.iterrows():

                if "account_name" in df.columns and "account_name_id" not in df.columns:
                    account = CardAccount.objects.get(user=self.user, name=row["account_name"])
                elif "account_name_id" in df.columns and "account_name" not in df.columns:
                    account = self.cards_dict[row["account_name_id"]]
                else:
                    raise Exception("Account name or account id must be provided")
            
                if "category_name" in df.columns and "category_id" not in df.columns:
                    category = Category.objects.get(user=self.user, name=row["category_name"])
                elif "category_id" in df.columns and "category_name" not in df.columns:
                    category = self.categories_dict[row["category_id"]]
                else:
                    raise Exception("Category name or category id must be provided")
                
                try:
                    expense = Expense(
                        user=self.user,
                        description=row["description"],
                        date=row["date"],
                        amount=row["amount"],
                        account_name=account,
                        category=category
                    )
                    expense.save()
                except Exception as e:
                    print(colorama.Fore.RED + f"Error importing {row}" + colorama.Style.RESET_ALL)
                    print(e)
                    print(f"Error importing {row}")
        
            print("Successfully imported expenses")

        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
            print(e)

    def import_incomes(self):
        print("Importing incomes")
        try:
            data = self.workbook.worksheet("income")
            df = pd.DataFrame(data.get_all_records())
            print(df.head())

            for _, row in df.iterrows():
                if "account_name" in df.columns and "account_id" not in df.columns:
                    account = Account.objects.get(user=self.user, name=row["account_name"])
                elif "account_id" in df.columns and "account_name" not in df.columns:
                    account = self.accounts_dict[row["account_id"]]
                else:
                    raise Exception("Account name or account id must be provided")
                
                income = Income(
                    user=self.user,
                    description=row["description"],
                    date=row["date"],
                    amount=row["amount"],
                    account_name=account
                )
                income.save()

            print("Successfully imported incomes")
        except Exception as e:
            print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
            print(e)
