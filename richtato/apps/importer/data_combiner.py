import pandas as pd

#when using this code it can only handle one data sheet at a time. im not sure how to make it handle multiple sheets at a time.

def organize_bank_statement (master_data_sheet,imported_data_sheet_set,bank_name):
   for imported_data_sheet in imported_data_sheet_set: 
      master_data_sheet = pd.DataFrame()
      if bank_name.lower() == "bank of america":
         organize_bofa_statement(master_data_sheet,imported_data_sheet,bank_name)
      if bank_name.lower() == "amex":
         organize_amex_statement(master_data_sheet,imported_data_sheet,bank_name)
      if bank_name.lower() == "citibank":
         organize_citi_statement(master_data_sheet,imported_data_sheet,bank_name)

def organize_bofa_statement (master_data_sheet,imported_data_sheet,bank_name):
   df_table = pd.read_csv(imported_data_sheet, header=2)
   df_table = df_table.rename(columns={
      'Posted_Date': 'Date',
      'Payee': 'Description'
   })
   df_table = df_table[['Date', 'Description', 'Amount']]
   df_table['Category'] = 'Uncategorized'
   df_table['Card'] = bank_name
   master_data_sheet = pd.concat([master_data_sheet, df_table], ignore_index=True)
   return master_data_sheet[['Date', 'Description', 'Amount','Category','Card']]

def organize_amex_statement (master_data_sheet,imported_data_sheet,bank_name):
   df_table = pd.read_csv(imported_data_sheet, header=2)
   df_table = df_table[['Date', 'Description', 'Debit','Credit']]
   df_table['Amount'] = df_table['Debit'] + df_table['Debit']
   df_table['Category'] = 'Uncategorized'
   df_table['Card'] = bank_name
   master_data_sheet = pd.concat([master_data_sheet, df_table], ignore_index=True)
   return master_data_sheet[['Date', 'Description', 'Amount','Category','Card']]

def organize_citi_statement (master_data_sheet,imported_data_sheet,bank_name):
   df_table = pd.read_excel(imported_data_sheet, header=2)
   df_table = df_table[['Date', 'Description', 'Amount']]
   df_table['Category'] = 'Uncategorized'
   df_table['Card'] = bank_name
   master_data_sheet = pd.concat([master_data_sheet, df_table], ignore_index=True)
   return master_data_sheet[['Date', 'Description', 'Amount','Category','Card']]

