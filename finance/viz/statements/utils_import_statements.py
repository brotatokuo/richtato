import pandas as pd
import colorama
import os, warnings, re
from datetime import datetime
from django.http import HttpResponse
from viz.models import Category, Transaction, Account, User, CardAccount
from viz.ai.utils_ai import ai_description_simplifier, ai_auto_categorization
import time

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
statements_folder_path = os.path.join((os.path.dirname(os.getcwd())), "Statements")

def sort_statements_and_generate_csv(request) -> None:
    print("Folders in statements_folder_path", os.listdir(statements_folder_path))

    bank_list = [folder for folder in os.listdir(statements_folder_path) if os.path.isdir(os.path.join(statements_folder_path, folder))]
    print("Banks: ", bank_list)

    df_combined = pd.DataFrame()
    for bank_name in bank_list:
        folder_path = os.path.join(statements_folder_path, bank_name)
        
        if "amex" in bank_name.lower() or "american express" in bank_name.lower():
            df = handle_amex_statements(folder_path, bank_name)
        elif "citi" in bank_name.lower():
            df = handle_citi_statements(folder_path, bank_name)
        elif "bank of america" in bank_name.lower():
            df = handle_bofa_statements(folder_path, bank_name)
        else:
            print(colorama.Fore.RED + f"Bank {bank_name} not supported" + colorama.Style.RESET_ALL)
            assert False, f"Bank {bank_name} not supported"
        df_combined = pd.concat([df_combined, df], ignore_index=True)

        output_filename = f"viz/static/historic_data/alan_{datetime.now().strftime('%Y%m%d')}.csv"
        df_combined.to_csv(output_filename, index=False)

    print(colorama.Fore.GREEN + "All statements processed." + colorama.Style.RESET_ALL)
    return HttpResponse(f"Statements sorted and saved to {output_filename}")

def handle_amex_statements(folder_path, bank):
    """
    Handle American Express statements and compile them into a single DataFrame with the columns:
    Date, Description, Amount, Category, Card.
    
    Arguments:
    - folder_path: Path to the folder containing the statements.
    - bank: The name of the bank (e.g., "Amex") to identify the card type.
    """
    count = 0
    statements_list = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
    df_combined = pd.DataFrame()  # This will hold all the combined statements
    
    for statement in statements_list:
        excel_path = os.path.join(folder_path, statement)
        
        df = pd.read_excel(excel_path, header=None, engine='openpyxl')
        
        # Extract account/card number or identifier
        text = df.iloc[0, 1]
        account = re.split(r'\/', text, maxsplit=1)[0].strip()
        
        # Read the actual statement data (assuming the table starts at row 6)
        df_table = pd.read_excel(excel_path, header=6, engine='openpyxl')
        
        # Ensure the relevant columns (Date, Description, Amount) are present
        # If necessary, rename them or adjust based on the structure of your data
        df_table = df_table[['Date', 'Description', 'Amount']]
        
        # Add the 'Category' column - you can adjust how you define the category
        # For now, we'll just put a placeholder "Uncategorized"
        df_table['Category'] = 'Uncategorized'
        
        # Add the 'Card' column - this will hold the card/account information
        df_table['Card'] = account
        
        # Append the processed statement to the combined DataFrame
        df_combined = pd.concat([df_combined, df_table], ignore_index=True)
        
        # Rename the statement file based on account and date range
        min_date = min(df_table['Date'])
        max_date = max(df_table['Date'])
        rename_statements(excel_path, folder_path, bank, account, min_date, max_date)
        
        count += 1

    print(colorama.Fore.YELLOW + f"Renamed {count} statements for {bank}" + colorama.Style.RESET_ALL)
    return df_combined[["Card", "Date", "Description", "Amount", "Category"]]
    

def handle_citi_statements(folder_path, bank):
    """
    Handle Citi statements and compile them into a single DataFrame with the columns:
    Date, Description, Amount, Category, Card.
    
    Arguments:
    - folder_path: Path to the folder containing the statements.
    - bank: The name of the bank (e.g., "Citi") to identify the card type.
    """
    count = 0
    statements_list = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
    df_combined = pd.DataFrame()  # This will hold all the combined statements
    
    for statement in statements_list:
        excel_path = os.path.join(folder_path, statement)
        df = pd.read_csv(excel_path, header=0)
        
        # Assuming the CSV has 'Date', 'Description', 'Amount' columns
        df_table = df[['Date', 'Description', 'Debit', 'Credit']]

        # Combine 'Debit' and 'Credit' columns to get the 'Amount' column
        df_table['Amount'] = df_table['Debit'].fillna(0) + df_table['Credit'].fillna(0)
        
        # Add 'Category' column (default to 'Uncategorized' for now)
        df_table['Category'] = 'Uncategorized'
        
        # Determine the card type based on the columns in the CSV
        if "Member Name" in df.columns.to_list():  # Costco
            card_type = "Costco"
        else:
            card_type = "Custom Cash"
        
        # Add 'Card' column
        df_table['Card'] = card_type
        
        # Append the processed statement to the combined DataFrame
        df_combined = pd.concat([df_combined, df_table], ignore_index=True)
        
        # Extract date range for renaming purposes
        min_date = min(df_table['Date'])
        max_date = max(df_table['Date'])
        
        # Rename the statement file
        rename_statements(excel_path, folder_path, bank, card_type, min_date, max_date)
        
        count += 1
    
    print(colorama.Fore.GREEN + f"Renamed {count} statements for {bank}" + colorama.Style.RESET_ALL)
    return df_combined[["Card", "Date", "Description", "Amount", "Category"]]
    
def handle_bofa_statements(folder_path, bank):
    """
    Handle Bank of America (BoA) statements and compile them into a single DataFrame with the columns:
    Date, Description, Amount, Category, Card.
    
    Arguments:
    - folder_path: Path to the folder containing the statements.
    - bank: The name of the bank (e.g., "BoA") to identify the card type.
    """
    count = 0
    statements_list = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
    df_combined = pd.DataFrame()  # This will hold all the combined statements
    
    for statement in statements_list:
        excel_path = os.path.join(folder_path, statement)
        
        # Read the CSV file (assuming it has columns 'Date', 'Description', 'Amount')
        df = pd.read_csv(excel_path, header=0)
        
        # Ensure the DataFrame has the expected columns (adjust as needed)
        df_table = df[['Posted Date', 'Payee', 'Amount']]
        df_table.rename(columns={'Posted Date': 'Date'}, inplace=True)
        df_table.rename(columns={'Payee': 'Description'}, inplace=True)
        
        # Add a 'Category' column (default to 'Uncategorized' for now)
        df_table['Category'] = 'Uncategorized'
        
        # Add a 'Card' column - indicating the type of BoA card/account
        df_table['Card'] = "Bank of America Custom Cash Rewards"
        
        # Append the processed statement to the combined DataFrame
        df_combined = pd.concat([df_combined, df_table], ignore_index=True)
        
        print(df_table.head())
        min_date = min(df_table['Date'])
        max_date = max(df_table['Date'])
        
        rename_statements(excel_path, folder_path, bank, "Custom Cash", min_date, max_date)
        
        count += 1

    print(f"Processed {count} BoA statements.")
    return df_combined[["Card", "Date", "Description", "Amount", "Category"]]

def date_formatter(date) -> str:
    date_obj = datetime.strptime(str(date), "%m/%d/%Y")
    # Format the date object to the desired format (YYYYMonDD)
    formatted_start_date = date_obj.strftime("%Y%b%d")
    return formatted_start_date

def rename_statements(excel_path, folder_path, bank, account, min_date, max_date) -> None:
    start_date = date_formatter(min_date)
    end_date = date_formatter(max_date)
    if ".csv" in excel_path:
        suffix = "csv"
    else:
        suffix = "xlsx"
    new_name = f"{bank} [{account}] ({start_date}-{end_date}).{suffix}"
    new_path = os.path.join(folder_path, new_name)
    os.rename(excel_path, new_path)
    print(colorama.Fore.GREEN + f"{new_name}" + colorama.Style.RESET_ALL)

def import_statements(request):
    # Helper function to save a transaction
    def save_transaction(user, account, description, category, date, amount):
        transaction = Transaction(
            user=user,
            account_name=account,
            description=description,
            category=category,
            date=date,
            amount=amount,
        )
        transaction.save()
    
    # Helper function to handle rate-limited AI calls
    def get_category_with_ai(description, categories, call_counter, start_time):
        if call_counter < 15:
            category = ai_auto_categorization(description, [category.name for category in categories])
            call_counter += 1
        else:
            # Calculate elapsed time and wait for the remaining seconds
            elapsed_time = time.time() - start_time
            if elapsed_time < 60:
                time.sleep(60 - elapsed_time)  # Wait for the remaining time to complete 1 minute
            # Reset call counter and start time
            call_counter = 1
            start_time = time.time()
            # Make the next AI call after resetting
            category = ai_auto_categorization(description, [category.name for category in categories])
        return category, call_counter, start_time

    # Get the user from the request
    user = User.objects.get(username=request.user)
    
    # Load all categories and accounts at once
    categories = Category.objects.filter(user=user)
    account_list = list(CardAccount.objects.filter(user=user).values_list('name', flat=True))

    # Initialize counters and start time for API rate-limiting
    transactions_processed = 0
    call_counter = 0
    start_time = time.time()

    # Load the combined CSV file
    file_name = "viz/static/historic_data/import.csv"
    df_combined = pd.read_csv(file_name)

    try:
        total = len(df_combined)
        for index, row in df_combined.iterrows():
            description = simplify_description(row['Description']).lower().strip()
            amount = round(float(row['Amount']), 2)
            date = datetime.strptime(row['Date'], '%m/%d/%Y').strftime('%Y-%m-%d')
            account = row['Card']

            # Check if there is an identical entry in the database
            if Transaction.objects.filter(user=user, description=description, amount=amount, date=date, account_name__name=account).exists():
                print(f"Skipping duplicate: {description} | {amount} | {date} | {account}")
                continue

            print(f"Processing: {description} | Amount: {amount} | Date: {date} | Account: {account}")

            # Check if account exists for the user
            if account not in account_list:
                print(colorama.Fore.RED + "Users available accounts: " + str(account_list) + colorama.Style.RESET_ALL)
                return HttpResponse(f"Account {account} not found in available accounts. Please add the account first.")

            # Search for a category based on the description
            description_words = description.split()
            category_instance = None
            for word in description_words:
                print(f"Searching for: {word}")
                category_instance = categories.filter(keywords__icontains=word).first()
                if category_instance:
                    print(f"Category found: {category_instance.name}")
                    break

            if category_instance == None:
                print("\033[95mUsing AI to determine category\033[0m")
                category_name, call_counter, start_time = get_category_with_ai(description, categories, call_counter, start_time)
                print(f"Category found by AI: {category_name} | Call counter: {call_counter}")
                category_instance = categories.get(name=category_name)

            # Create and save the transaction
            try:
                account_instance = CardAccount.objects.get(user=user, name=account)
                save_transaction(user, account_instance, description, category_instance, date, amount)
                transactions_processed += 1
            except (CardAccount.DoesNotExist, Category.DoesNotExist) as e:
                print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
                return HttpResponse(f"Error: {str(e)}")
    except Exception as e:
        print(colorama.Fore.RED + str(e) + colorama.Style.RESET_ALL)
        # Save df
        unprocessed_df = df_combined.iloc[index:]
        unprocessed_df.to_csv(file_name, index=False)
        return HttpResponse(f"Error: {str(e)}")
    return HttpResponse(f"Processed {transactions_processed} out of {total} transactions.")


def simplify_description(description):
    """
    Simplify the description if too long ai_description_simplifier 
    """
    print(f"Original description: {description}")
    simple_description = None
    if "delta" in description.lower():
            description = "Delta Airlines"
    elif "eva air" in description.lower():
        simple_description = "EVA Air"
    elif "jetblue" in description.lower():
        simple_description = "JetBlue Airways"
    elif "southwest" in description.lower():
        simple_description = "Southwest Airlines"
    elif "united" in description.lower():
        simple_description = "United Airlines"
    elif "american airlines" in description.lower():
        simple_description = "American Airlines"
    elif "spirit airlines" in description.lower():
        simple_description = "Spirit Airlines"
    elif "alaska air" in description.lower():
        simple_description = "Alaska Airlines"
    elif "frontier airlines" in description.lower():
        simple_description = "Frontier Airlines"

    if simple_description:
        return simple_description

    words_to_remove = ["AplPay"]
    for word in words_to_remove:
        description = description.replace(word, "")
    description = description.strip()

    if len(description) > 40:
            description = ai_description_simplifier(description)
    print(f"Simplified description: {description}")
    return description


def test_category_search(request):
    categories = Category.objects.filter(user=request.user)
    print(categories)

    # description = 'WHOLEFDS ANN ARBOR'
    description_words = ['wholefds', 'crb', 'ann', 'arbor', 'mi']
    
    # Try to find a category for any word in the description
    for word in description_words:
        # Check if any category matches the current word
        category = categories.filter(keywords__icontains=word.lower()).first()
        if category:
            return HttpResponse(f"Category found: {category.name}")  # Return as soon as a match is found
    return HttpResponse("Category not found")