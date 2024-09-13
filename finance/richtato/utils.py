import pandas as pd
import os, warnings, re
from datetime import datetime
from django.http import HttpResponse
from richtato.models import *
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

script_path = os.path.abspath(__file__)
parent_path = os.path.dirname(script_path)

# data_folder_path = r"C:\Users\Alan\OneDrive\Desktop\Richtato\finance\richtato\static\data"
data_folder_path = os.path.join(parent_path, "static/data")
card_statements_folder_path = os.path.join(data_folder_path, "Credit Card Statements")
# card_statements_folder_path = r"C:\Users\Alan\OneDrive\Desktop\Richtato\finance\richtato\static\data\Credit Card Statements"

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

def structure_statements():
    return None            
            
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

    # Cleanup Data
    master_df = master_df[~master_df['Description'].str.contains("MOBILE PAYMENT", case=False, na=False)]
    master_df = master_df[~master_df['Description'].str.contains("ONLINE PAYMENT", case=False, na=False)]

    # Categorization
    master_df['Category'] = master_df.apply(lambda row: auto_categorization(row['Description'], row['Account Name']), axis=1)

    # Sort by Date
    master_df['Date'] = pd.to_datetime(master_df['Date'])
    master_df = master_df.sort_values(by="Date")
   

    # Add Year, Month, Day
    master_df['Year'] = master_df['Date'].dt.year
    master_df['Month'] = master_df['Date'].dt.month
    master_df['Day'] = master_df['Date'].dt.day
    master_df['Date'] = pd.to_datetime(master_df['Date']).dt.date

    master_df_path = os.path.join(data_folder_path, "master_creditcard_data.xlsx")
    master_df.to_excel(master_df_path, index=False)

    master_df['Date'] = pd.to_datetime(master_df['Date'], format='%m/%d/%Y')

    # Save to database
    for _, row in master_df.iterrows():
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
    print(f"\033]8;;{master_df_path}\033\\\033[93mClick to open Master Data\033[0m\033]8;;\033\\")


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