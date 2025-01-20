import os
import warnings
import colorama
import pandas as pd
from apps.expense.models import Category, Expense
from apps.income.models import Income
from apps.account.models import Account, AccountTransaction
from apps.richtato_user.models import CardAccount, Category

# from utilities.ai import AI

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
statements_folder_path = os.path.join((os.path.dirname(os.getcwd())), "Statements")
