import os
import re
from abc import ABC, abstractmethod

import pandas as pd
from loguru import logger

# Optional imports
from openai import OpenAI as OpenAIClient

from apps.richtato_user.models import Category, User


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

    def get_user_categories(self, user: User) -> list[str]:
        return list(
            Category.objects.filter(user=user)
            .exclude(name="Unknown")
            .values_list("name", flat=True)
        )

    def categorize_transaction(self, user: User, input: str) -> str:
        category_list = self.get_user_categories(user)
        category_string = ", ".join(category_list)
        prompt = f"""
        Given the following categories: {category_string}
        Which category best matches the input text: "{input}"?
        Please choose only from the given categories.
        """

        response = self._ask(prompt)
        return response

    def categorize_dataframe(self, user: User, df: pd.DataFrame) -> pd.DataFrame:
        """
        Categorizes all rows in the DataFrame based on the 'Description' column in a single prompt.
        """
        if "Description" not in df.columns:
            raise ValueError("DataFrame must contain a 'Description' column.")

        # Get user's categories
        categories = self.get_user_categories(user)
        category_string = ", ".join(categories)

        descriptions = df["Description"].tolist()

        # Build and send the prompt
        prompt = self._build_batch_prompt(descriptions, category_string)
        response = self._ask(prompt)

        # Parse LLM response
        predicted = self._parse_batch_response(response, descriptions)
        df["Category"] = predicted
        logger.info(
            f"Categorization Completed: {len(predicted)} transactions categorized."
        )
        logger.debug(df)
        return df

    def _build_batch_prompt(self, descriptions: list[str], category_string: str) -> str:
        lines = "\n".join(f"{i + 1}. {desc}" for i, desc in enumerate(descriptions))
        prompt = f"""
            You are a financial categorization assistant.

            Given the following list of categories:
            {category_string}

            Please categorize the following transactions using only one of the above categories for each.

            Transactions:
            {lines}

            Respond in the format:
            1: <Category>
            2: <Category>
            ...
            """
        return prompt

    def _parse_batch_response(self, response: str, batch: list[str]) -> list[str]:
        matches = re.findall(r"(\d+):\s*(.+)", response)
        mapping = {int(i): cat.strip() for i, cat in matches}
        return [mapping.get(i + 1, "Unknown") for i in range(len(batch))]
