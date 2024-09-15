import pandas as pd
import os, warnings, re
from datetime import datetime
from django.http import HttpResponse
from viz.models import *
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

script_path = os.path.abspath(__file__)
parent_path = os.path.dirname(script_path)

data_folder_path = os.path.join(parent_path, "static/data")
card_statements_folder_path = os.path.join(data_folder_path, "Credit Card Statements")

script_path = os.path.abspath(__file__)
parent_path = os.path.dirname(script_path)
print("card statements path", card_statements_folder_path)

def sort_statements():
    bank_list = [folder for folder in os.listdir(card_statements_folder_path)  if os.path.isdir(os.path.join(card_statements_folder_path, folder))]

    for bank in bank_list:
        folder_path = os.path.join(card_statements_folder_path, bank)
        
        # Rename Statements
        if bank == "American Express":
            statements_list = [file for file in os.listdir(folder_path)  if os.path.isfile(os.path.join(folder_path, file))]
            for statement in statements_list:
                if ".xlsx" in statement and ".csv" not in statement:
                    # print("Statement:", statement)
                    excel_path = os.path.join(folder_path, statement)
                    # print("Excel Path:", excel_path)
                    df = pd.read_excel(excel_path, header=None, engine='openpyxl')

                    text = df.iloc[0,1]
                    account = re.split(r'\/', text, maxsplit=1)[0]

                    # Date Range
                    df_table = pd.read_excel(excel_path, header=6, engine='openpyxl')
                    min_date = min(df_table['Date'])
                    max_date = max(df_table['Date'])
                    rename_statements(excel_path, folder_path, bank, account, min_date, max_date)

        elif bank == "Citi":
            statements_list = [file for file in os.listdir(folder_path)  if os.path.isfile(os.path.join(folder_path, file))]
            for statement in statements_list:
                excel_path = os.path.join(folder_path, statement)
                df = pd.read_csv(excel_path, header=0)

                # Date Range
                min_date = min(df['Date'])
                max_date = max(df['Date'])

                # Diffrentiate Costco vs Custom Cash
                if "Member Name" in df.columns.to_list(): # Costco
                    rename_statements(excel_path, folder_path, bank, "Costco", min_date, max_date)
                else:
                    rename_statements(excel_path, folder_path, bank, "Custom Cash", min_date, max_date)

def rename_statements(excel_path, folder_path, bank, account, min_date, max_date):
    def date_formatter(date):
        date_obj = datetime.strptime(str(date), "%m/%d/%Y")
        # Format the date object to the desired format (YYYYMonDD)
        formatted_start_date = date_obj.strftime("%Y%b%d")
        return formatted_start_date

    start_date = date_formatter(min_date)
    end_date = date_formatter(max_date)
    if ".csv" in excel_path:
        suffix = "csv"
    else:
        suffix = "xlsx"
    new_name = os.path.join(folder_path, f"{bank} [{account}] ({start_date}-{end_date}).{suffix}")
    os.rename(excel_path, new_name)
            
def compile_statements():
    bank_list = [folder for folder in os.listdir(card_statements_folder_path)  if os.path.isdir(os.path.join(card_statements_folder_path, folder))]
    print("bank_list:", bank_list)
    master_df = pd.DataFrame()
    # Regex pattern to find text between square brackets
    pattern = r'\[([^\]]+)\]'

    for bank in bank_list:
        print("bank:", bank)
        folder_path = os.path.join(card_statements_folder_path, bank)
        statements_list = [file for file in os.listdir(folder_path)  if os.path.isfile(os.path.join(folder_path, file))]

        if bank == "American Express":
            header_no = 6
        elif bank == "Citi":
            header_no = 0

        for statement in statements_list:
            if ".xlsx" in statement or ".csv" in statement:
                account_name = re.search(pattern, statement).group(1)
                excel_path = os.path.join(card_statements_folder_path, bank, statement)   
                if "Citi" in excel_path:
                    df = pd.read_csv(excel_path, header=header_no)
                    df['Amount'] = df['Debit'].fillna(0) + df['Credit'].fillna(0)

                    # if "[Costco]" in excel_path:
                    #     df = df[df['Member Name'] == "KUO YUEH-LUNG"]
                else:
                    df = pd.read_excel(excel_path, header=header_no, engine='openpyxl')
                df['Account Name'] = account_name
                df = df[['Date', 'Account Name', 'Description', 'Amount']]
                master_df = pd.concat([master_df, df])

                # print("Account Name:", account_name)
                # print("EXCEL PATH :", excel_path)
                # print(df.head())

    # Save to Excel
    master_df.to_excel(os.path.join(data_folder_path, "Master Statements.xlsx"), index=False)
    return master_df

def categorize_transactions(df):
    # Convert 'Date' to datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Convert 'Amount' to numeric
    df['Amount'] = round(pd.to_numeric(df['Amount'], errors='coerce'), 2)

    # Handle missing values if necessary (optional)
    df = df.dropna()  # or use fillna()

    # Select specific columns in the desired order
    df = df[["Date", "Account Name", "Description", "Amount"]]
    df = df.sort_values(by="Date", ascending=True)

    # Categorization
    def form_category_dictionary():
        categories = Category.objects.all().values()
        categories_dict = {}
        for category in categories:
            categories_dict[category['name']] = category['keywords']

        # print("\nCategory Dictionary: ", categories_dict)
        return categories_dict
    
    category_dictionary = form_category_dictionary()

    def auto_categorization(description, account, category_dictionary):
        description = description.lower()
        for category, keywords in category_dictionary.items():
            # Split the keywords string into a list
            keyword_list = [keyword.strip() for keyword in keywords.split(",")]
            
            for keyword in keyword_list:
                if keyword.lower() in description:
                    # print("Description: ", description)
                    # print("Matched Keyword: ", keyword)
                    # print("Category: ", category)
                    # print("\n")
                    return category
                
        # Additional account-based categorization
        if account == "Costco":
            return "Costco Uncategorized"
        elif account == "Custom Cash":
            return "Dining (Auto)"
        else:
            return "Error"
            
    # print("Category Dictionary: ", category_dictionary)
    df['Category'] = df.apply(lambda row: auto_categorization(row['Description'], row['Account Name'], category_dictionary), axis=1)
    return df
    
def post_to_sql(df, request_user):
    for _, row in df.iterrows():
        exists = Transaction.objects.filter(
            user = request_user,
            account_name=row['Account Name'],
            description = row['Description'],
            date=row['Date'],
            amount = row['Amount']

        ).exists()

        if not exists:
            Transaction.objects.create(
                user = request_user,
                account_name=row['Account Name'],
                description = row['Description'],
                category = row['Category'],
                date=row['Date'],
                amount = row['Amount']
            )
    print("\033[92mSuccess!\033[0m")

def get_sql_data():
    transactions = Transaction.objects.all().values()
    df_transactions = pd.DataFrame(transactions)
    if df_transactions.empty:
        print("utils.py: No data found in the database. Import data first.")
        return df_transactions
    else:
        df_transactions = df_transactions.rename(columns={"date": "Date", "account_name": "Account Name", "description": "Description", "amount": "Amount", "category": "Category"})
        df_transactions = df_transactions.drop(columns=["id"])

        # Convert 'Date' to datetime
        df_transactions['Date'] = pd.to_datetime(df_transactions['Date'], errors='coerce')

        # Convert 'Amount' to numeric
        df_transactions['Amount'] = pd.to_numeric(df_transactions['Amount'], errors='coerce')

        # Handle missing values if necessary (optional)
        df_transactions = df_transactions.dropna()  # or use fillna()

        # Select specific columns in the desired order
        df_transactions = df_transactions[["Date", "Account Name", "Description", "Amount", "Category"]]
        df_transactions = df_transactions.sort_values(by="Date", ascending=True)
        
        # Cleanup Data
        df_transactions = df_transactions[~df_transactions['Description'].str.contains("MOBILE PAYMENT", case=False, na=False)]
        df_transactions = df_transactions[~df_transactions['Description'].str.contains("ONLINE PAYMENT", case=False, na=False)]

        # Sort by Date
        df_transactions['Date'] = pd.to_datetime(df_transactions['Date'])
        df_transactions = df_transactions.sort_values(by="Date")
    
        # Add Year, Month, Day
        df_transactions['Year'] = df_transactions['Date'].dt.year
        df_transactions['Month'] = df_transactions['Date'].dt.month
        df_transactions['Day'] = df_transactions['Date'].dt.day
        df_transactions['Date'] = pd.to_datetime(df_transactions['Date']).dt.date
        df_transactions['Date'] = pd.to_datetime(df_transactions['Date'], format='%m/%d/%Y')

        return df_transactions

def color_picker(i):
    # Preset colors
    colors = [
    "152,204,44",    # Green
    "255,99,132",    # Red
    "54,162,235",    # Blue
    "255,159,64",    # Orange
    "153,102,255",   # Purple
    "255,206,86",    # Yellow
    "75,192,192",    # Teal
    "255,99,177",    # Pink
    "0,255,255",     # Cyan
    "54,54,235"      # Dark Blue
]
    
    if i+1 > len(colors):
        color = "0,0,0" #black
    else:
        color = colors[i]

    background_color = f"rgba({color}, 0.4)"
    border_color = f"rgba({color}, 1)"
    return background_color, border_color