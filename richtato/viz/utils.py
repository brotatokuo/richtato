import pandas as pd
import os, warnings, re
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from viz.models import *
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

script_path = os.path.abspath(__file__)
parent_path = os.path.dirname(script_path)

data_folder_path = os.path.join(parent_path, "static/data")
card_statements_folder_path = os.path.join(data_folder_path, "Credit Card Statements")

script_path = os.path.abspath(__file__)
parent_path = os.path.dirname(script_path)
print("card statements path", card_statements_folder_path)

# region Excel Functions
def sort_statements()->None:
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

def rename_statements(excel_path, folder_path, bank, account, min_date, max_date) -> None:
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
            
def compile_statements()->pd.DataFrame:
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

    # Save to Excel
    master_df.to_excel(os.path.join(data_folder_path, "Master Statements.xlsx"), index=False)
    return master_df

# endregion

# region Category Functions
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
    def form_category_dictionary() -> dict:
        categories = Category.objects.all().values()
        categories_dict = {}
        for category in categories:
            categories_dict[category['name']] = category['keywords']

        # print("\nCategory Dictionary: ", categories_dict)
        return categories_dict
    
    category_dictionary = form_category_dictionary()

    def auto_categorization(description, account, category_dictionary, verbose=False):
        description = description.lower()
        for category, keywords in category_dictionary.items():
            # Split the keywords string into a list
            keyword_list = [keyword.strip() for keyword in keywords.split(",")]
            
            for keyword in keyword_list:
                if keyword.lower() in description:
                    if verbose:
                        print("Description: ", description)
                        print("Matched Keyword: ", keyword)
                        print("Category: ", category)
                        print("\n")
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
# endregion

# region SQL Functions    
def post_to_sql(df, request_user)->None:
    """
    Post the dataframe to the SQL database
    """
    for _, row in df.iterrows():
        Transaction.objects.get_or_create(
            user=request_user,
            account_name=row['Account Name'],
            description=row['Description'],
            date=row['Date'],
            amount=round(row['Amount'], 2),
            defaults={
                'category': row['Category']
            }
        )
    print("\033[92mSuccess!\033[0m")

def get_sql_data(user, context="Spending", verbose=False):
    if context == "Spending":
        dict = Transaction.objects.filter(user=user).select_related('account_name', 'category').values(
            'id', 'date', 'amount', 'account_name__name', 'category__name', 'description'
        )
        df = pd.DataFrame(list(dict))
    else:
        context = "Earnings"
        dict = Earning.objects.filter(user=user).select_related('account_name').values(
            'id', 'date', 'amount', 'account_name__name', 'description'
        )
        df = pd.DataFrame(list(dict)
                                       )
    if verbose:
        print("User Accounts Dataframe:", dict)
        print("User Transactions Dataframe:", df)
    
    if df.empty:
        print("No data found in the database. Import data first.")
    else:
        df = strcuture_sql_data(df, context=context, verbose=False)    
    return df
    
def strcuture_sql_data(df, context, verbose):
    if verbose:
        print("Structure SQL Data")
        print(df.head())

    # Organize Columns
    if context == "Spending":
        df = df.rename(columns={"date": "Date", "account_name__name": "Account Name", "description": "Description", "amount": "Amount", "category__name": "Category"})
        df = df[["Date", "Account Name", "Description", "Amount", "Category"]]
    else:
        df = df.rename(columns={"date": "Date", "account_name__name": "Account Name", "description": "Description", "amount": "Amount"})
        df = df[["Date", "Account Name", "Description", "Amount"]]

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.sort_values(by="Date", ascending=True)

    if verbose:
        print("Renamed and Organized Columns")
        print(df.head())

    # Cleanup Data
    df = df[~df['Description'].str.contains("MOBILE PAYMENT", case=False, na=False)]
    df = df[~df['Description'].str.contains("ONLINE PAYMENT", case=False, na=False)]

    # Add Year, Month, Day
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y').dt.date
    
    if verbose:
        print("Structured Transactions Data")
        print(df.head())
    return df

# endregion

# region Helper functions
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

# endregion