import os
import google.generativeai as genai
from fuzzywuzzy import fuzz

# Suppress logging warnings
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
API_KEY = os.environ.get("API_KEY")
genai.configure(api_key=API_KEY)  # Ensure the right key is used
model = genai.GenerativeModel("gemini-1.5-flash")

def ai_description_simplifier(input_text):
    
    prompt = f"""
    Simplify this transcation description: "{input_text}", into a more concise description. 
    """
    result = model.generate_content([prompt])
    best_match = result.text.strip()

    return best_match

def ai_auto_categorization(input_text, category_list) -> str:
    """
    Given an input text and a list of categories, use AI to determine the best category match for the input text.
    Automatically categorizes card payments --> "Card Payments"
    """
    category_list.append("Card Payments")
    category_string = ", ".join(category_list)

    prompt = f"""
    Given the following categories: {category_string    }
    Which category best matches the input text: "{input_text}"?
    Please choose only from the given categories.
    """

    result = model.generate_content([prompt])
    model_response = result.text.strip()

    # Exact match
    if model_response in category_list:
        return model_response

    # Fuzzy matching
    best_match = max(category_list, key=lambda x: fuzz.ratio(x, model_response))
    print(f'\033[96mInput: "{input_text}" | AI Response: "{model_response}" | Best Match: "{best_match}"\033[0m')
    return best_match
