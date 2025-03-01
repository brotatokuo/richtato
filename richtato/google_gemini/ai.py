import os

import google.generativeai as genai
from fuzzywuzzy import fuzz

from richtato.apps.richtato_user.models import Category, User

API_KEY = os.environ.get("GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-1.5-flash-8b")


class AI:
    def __init__(self):
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash-8b")

    @classmethod
    def description_simplifier(cls, input: str) -> str:
        """
        Given a transaction description, use AI to simplify the description into a more concise form.
        """
        prompt = f"""
        Simplify this transcation description: "{input}", into a more concise description.
        """
        result = model.generate_content([prompt])
        best_match = result.text.strip()

        return best_match

    @classmethod
    def categorize_transaction(cls, user: User, input: str) -> str:
        """
        Given an input text and a list of categories, use AI to determine the best category match for the input text.
        """
        category_list = Category.objects.filter(user=user).values_list(
            "name", flat=True
        )
        category_string = ", ".join(category_list)
        prompt = f"""
            Given the following categories: {category_string}
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
