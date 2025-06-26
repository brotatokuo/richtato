import os
from abc import ABC, abstractmethod

import google.generativeai as genai
from fuzzywuzzy import fuzz
from loguru import logger

# Optional imports
from openai import OpenAI as OpenAIClient

from richtato.apps.richtato_user.models import Category, User


class BaseAI(ABC):
    @abstractmethod
    def simplify_description(self, input: str) -> str:
        pass

    @abstractmethod
    def categorize_transaction(self, user: User, input: str) -> str:
        pass


class OpenAI(BaseAI):
    def __init__(self):
        # Initialize the OpenAI client with API key
        self.client = OpenAIClient(api_key=os.environ["OPENAI_API_KEY"])
        self.model_name = "gpt-3.5-turbo"

    def _ask(self, prompt: str) -> str:
        # Use the new v1.0+ API syntax
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    def simplify_description(self, input: str) -> str:
        prompt = f"""Simplify this transaction description: "{input}", into a more concise description."""
        return self._ask(prompt)

    def categorize_transaction(self, user: User, input: str) -> str:
        category_list = list(
            Category.objects.exclude(name="Unknown").values_list("name", flat=True)
        )
        category_string = ", ".join(category_list)
        prompt = f"""
        Given the following categories: {category_string}
        Which category best matches the input text: "{input}"?
        Please choose only from the given categories.
        """

        response = self._ask(prompt)
        if response in category_list:
            return response

        best_match = max(category_list, key=lambda x: fuzz.ratio(x, response))
        logger.info(
            f'Input: "{input}" | AI Response: "{response}" | Best Match: "{best_match}"'
        )
        return best_match


class GeminiAI(BaseAI):
    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel("gemini-1.5-flash-8b")

    def _ask(self, prompt: str) -> str:
        response = self.model.generate_content([prompt])
        return response.text.strip()

    def simplify_description(self, input: str) -> str:
        prompt = f"""Simplify this transaction description: "{input}", into a more concise description."""
        return self._ask(prompt)

    def categorize_transaction(self, user: User, input: str) -> str:
        category_list = Category.objects.exclude(name="Unknown").values_list(
            "name", flat=True
        )
        category_string = ", ".join(category_list)
        prompt = f"""
        Given the following categories: {category_string}
        Which category best matches the input text: "{input}"?
        Please choose only from the given categories.
        """

        response = self._ask(prompt)
        if response in category_list:
            return response

        best_match = max(category_list, key=lambda x: fuzz.ratio(x, response))
        logger.info(
            f'Input: "{input}" | AI Response: "{response}" | Best Match: "{best_match}"'
        )
        return best_match
