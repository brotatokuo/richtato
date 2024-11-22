import os
import google.generativeai as genai
from fuzzywuzzy import fuzz
from models import User

API_KEY = os.environ.get("API_KEY")
genai.configure(api_key=API_KEY)  # Ensure the right key is used
model = genai.GenerativeModel("gemini-1.5-flash-8b")


class AI:
    def __init__(self):
        genai.configure(api_key=self.os.environ.get("API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-flash-8b")

    def description_simplifier(self, input: str) -> str:
        """
        Given a transaction description, use AI to simplify the description into a more concise form.
        """
        prompt = f"""
        Simplify this transcation description: "{input}", into a more concise description. 
        """
        result = model.generate_content([prompt])
        best_match = result.text.strip()

        return best_match

    def categorize_transaction(self, user: User, input: str) -> str:
        """
        Given an input text and a list of categories, use AI to determine the best category match for the input text.
        """
        category_string = ", ".join(user.catego

        prompt = f"""
            Given the following categories: {category_string    }
            Which category best matches the input text: "{input}"?
            Please choose only from the given categories.
            """

        result = model.generate_content([prompt])
        model_response = result.text.strip()

        if model_response in category_list:
            return model_response

        best_match = max(category_list, key=lambda x: fuzz.ratio(x, model_response))
        print(
            f'\033[96mInput: "{input}" | AI Response: "{model_response}" | Best Match: "{best_match}"\033[0m'
        )
        return best_match
