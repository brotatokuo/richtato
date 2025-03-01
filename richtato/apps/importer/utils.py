import os
import warnings

# from richtato.utilities.ai import AI

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
statements_folder_path = os.path.join((os.path.dirname(os.getcwd())), "Statements")
