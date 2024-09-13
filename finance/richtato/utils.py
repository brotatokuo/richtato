import pandas as pd
import os, warnings, re
from datetime import datetime
from django.http import HttpResponse
from richtato.models import *
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
                excel_path = os.path.join(folder_path, statement)
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

def date_formatter(date):
    date_obj = datetime.strptime(str(date), "%m/%d/%Y")
    # Format the date object to the desired format (YYYYMonDD)
    formatted_start_date = date_obj.strftime("%Y%b%d")
    return formatted_start_date

def rename_statements(excel_path, folder_path, bank, account, min_date, max_date):
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
    master_df = pd.DataFrame()
    # Regex pattern to find text between square brackets
    pattern = r'\[([^\]]+)\]'

    for bank in bank_list:
        folder_path = os.path.join(card_statements_folder_path, bank)
        statements_list = [file for file in os.listdir(folder_path)  if os.path.isfile(os.path.join(folder_path, file))]

        if bank == "American Express":
            header_no = 6
        elif bank == "Citi":
            header_no = 0

        for statement in statements_list:
            account_name = re.search(pattern, statement).group(1)
            print("Account Name:", account_name)
            excel_path = os.path.join(card_statements_folder_path, bank, statement)
            print("EXCEL PATH :", excel_path)
            if "Citi" in excel_path:
                df = pd.read_csv(excel_path, header=header_no)
                df['Amount'] = df['Debit'].fillna(0) + df['Credit'].fillna(0)

                if "[Costco]" in excel_path:
                    df = df[df['Member Name'] == "KUO YUEH-LUNG"]
            else:
                df = pd.read_excel(excel_path, header=header_no, engine='openpyxl')
            df['Account Name'] = account_name
            print(df.head())
            df = df[['Date', 'Account Name', 'Description', 'Amount']]
            master_df = pd.concat([master_df, df])
        return master_df
def get_sql_data():
    transactions = Transaction.objects.all().values()
    df_transactions = pd.DataFrame(transactions)
    df_transactions = df_transactions.rename(columns={"date": "Date", "account_name": "Account Name", "description": "Description", "amount": "Amount"})
    df_transactions = df_transactions.drop(columns=["id"])

    # Convert 'Date' to datetime
    df_transactions['Date'] = pd.to_datetime(df_transactions['Date'], errors='coerce')

    # Convert 'Amount' to numeric
    df_transactions['Amount'] = pd.to_numeric(df_transactions['Amount'], errors='coerce')

    # Handle missing values if necessary (optional)
    df_transactions = df_transactions.dropna()  # or use fillna()

    # Select specific columns in the desired order
    df_transactions = df_transactions[["Date", "Account Name", "Description", "Amount"]]
    df_transactions = df_transactions.sort_values(by="Date", ascending=True)
    
    # Cleanup Data
    df_transactions = df_transactions[~df_transactions['Description'].str.contains("MOBILE PAYMENT", case=False, na=False)]
    df_transactions = df_transactions[~df_transactions['Description'].str.contains("ONLINE PAYMENT", case=False, na=False)]

    # Categorization
    df_transactions['Category'] = df_transactions.apply(lambda row: auto_categorization(row['Description'], row['Account Name']), axis=1)

    # Sort by Date
    df_transactions['Date'] = pd.to_datetime(df_transactions['Date'])
    df_transactions = df_transactions.sort_values(by="Date")
   
    # Add Year, Month, Day
    df_transactions['Year'] = df_transactions['Date'].dt.year
    df_transactions['Month'] = df_transactions['Date'].dt.month
    df_transactions['Day'] = df_transactions['Date'].dt.day
    df_transactions['Date'] = pd.to_datetime(df_transactions['Date']).dt.date
    df_transactions['Date'] = pd.to_datetime(df_transactions['Date'], format='%m/%d/%Y')

    # Save to database
    for _, row in df_transactions.iterrows():
        exists = Transaction.objects.filter(
            account_name=row['Account Name'],
            description = row['Description'],
            date=row['Date'],
            amount = row['Amount']
            
        ).exists()

        if not exists:
            Transaction.objects.create(
                account_name=row['Account Name'],
                description = row['Description'],
                date=row['Date'],
                amount = row['Amount']
            )
    print("\033[92mSuccess!\033[0m")
    return df_transactions

def auto_categorization(description, account):
    description = description.lower()
    
    categories = {
        "Charging and Gas": ["tesla inc supercharger", "tesla","gas", "ev connect"],
        "Car Maintenance": ["geico", "auto wash",],
        "Parking": ["garage", "parking", "spothero", "parkinirvine", "berkeley-prkg", "holland state park", ],
        "Travel": ["expedia", "delta air", "united", "ua inflt", "alaska air", "greyhound",  "uscustoms", 
                   "tsa global entry", "southwest", "inn", "ventra"],
        "Rideshare": ["lyft", "uber", "rideshare",],
        "Groceries": ["whole foods", "wholefds", "trader joe", "meijer", "tokyo fish", "busch's",
                      "marianos", "osaka", "h mart"],
        "Shopping": ["amazon", "uniqlo", "dick's", "duty-free", "dirty labs", "sonos", "duty free",
                     "hanmoosyoping(joo)hygyeonggi-do", ],
        "Merchandise and Wholesale": ["target", "walmart", "wal-mart", "costco", "costco whse", "tj max", "home depot"],
        "Subscriptions": ["apple.com/bill", "membership fee"],
        "Insurance": ["insurance"],
        "Utilities": ["at&t"],
        "Medical": ["compassionate care",],
        "Dining": ["meet fresh", "tock", "sq", "tst", "sushi", "ramen", "chipotle", "in-n-out", 
            "catering", "restaurant", "kung fu tea", "starbucks", "the seoul", "subway", 
            "k&d bistro", "boyne mtn", "haidilao", "slurping turtle", "dumpling home", "domino's", "gen",
            "hancook", "macheko grille", "ann arbor cofann arbor", "sweetwaters", "coffee", "hand craft cosparks",
            "roseway sub", "noodle", "roundabout grsparks", "whitney peak reno", "sordetroit",
            "yogurt", "tea", "maison vervallejo", "rantei", "boba", "olive garden", "pearl river",
            "ginger deli", "snack*", "mendocino farms", "tous les jours", "dog patch sfo", "butch's dry dock",
            "noodles", "5guys", "obaitori"],
        "Fun":["golf", "ikon", "av ann arbor"],
        "Other": ["intuit *turbotax", "great clann", "great clips", "launchingdeals", "say ya photo", "sephora", 
                "usps", "u-haul"]
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in description:
                # print("Description: ", description)
                # print("Matched Keyword: ", keyword)
                # print("Category", category)
                # print("\n")
                return category
    if account == "Costco":
        return "Uncategorized"
    elif account == "Custom Cash":
        return "Dining (Auto)"
    else:
        return "Uncategorized"