import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_formatting import format_cell_range, CellFormat, TextFormat


class GoogleSheetsClient:

    def __init__(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("/Users/alan/Desktop/Richtato/richtato/utilities/google_drive/credentials/credentials.json", scopes=scopes)
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
