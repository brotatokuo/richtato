from abc import ABC, abstractmethod

import pandas as pd
from loguru import logger

from richtato.apps.expense.models import Expense


class CardCanonicalizer(ABC):
    """
    Abstract class for canonicalizing card data.
    """

    def __init__(self, user, card_name: str, df: pd.DataFrame):
        """
        Initializes the CardCanonicalizer with a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing card data.
        """
        self.user = user
        self.card_name = card_name
        self.df = df
        self.formatted_df = pd.DataFrame()
        self.output_columns = ["Card", "Date", "Description", "Amount", "Category"]
        self.format()

    @classmethod
    @abstractmethod
    def from_file(cls, card_name: str, file_path: str) -> pd.DataFrame:
        """
        Abstract method to be implemented by subclasses for reading card data from a file.
        """
        pass

    @property
    @abstractmethod
    def input_columns(self) -> list:
        """
        Abstract method to be implemented by subclasses for returning the input columns.
        """
        pass

    @abstractmethod
    def _format(self) -> None:
        """
        Abstract method to be implemented by subclasses for canonicalizing card data.
        """
        pass

    def format(self) -> pd.DataFrame:
        """
        Canonicalizes the given card data."
        """
        self._format()
        self.formatted_df["Card"] = self.card_name
        self._convert_date()
        self._convert_amount()
        self._compute_category()
        self.formatted_df.sort_values("Date", inplace=True)
        self.formatted_df.reset_index(drop=True, inplace=True)
        return self.formatted_df

    def check_input_format(self):
        """
        Checks if the input DataFrame has the required format.
        """
        if self.df.columns.tolist() != self.input_columns:
            logger.error("\n" + self.df.head().to_string())
            raise ValueError(
                f"Input DataFrame is not the expected format. Expected columns: {self.input_columns}"
            )

    def _convert_date(self) -> None:
        """
        Formats the date in the DataFrame to YYYY-MM-DD.
        """
        self.formatted_df["Date"] = pd.to_datetime(
            self.formatted_df["Date"]
        ).dt.strftime("%Y-%m-%d")

    def _convert_amount(self) -> None:
        """
        Converts the amount in the DataFrame to float.
        """
        self.formatted_df["Amount"] = self.formatted_df["Amount"].astype(float).round(2)
        self.formatted_df["Amount"] = self.formatted_df["Amount"].astype(float).round(2)

    def _compute_category(self) -> None:
        """
        Computes the category for each transaction in the DataFrame.
        """
        raise NotImplementedError("Implement smart categorization first")

    def process(self) -> None:
        """
        Iterate through card's formatted df and add each to the database.
        """

        for _, row in self.formatted_df.iterrows():
            description = row["Description"]
            category = row["Category"]
            date = row["Date"]
            amount = row["Amount"]

            transaction = Expense(
                user=self.user,
                account_name=self.card_name,
                description=description,
                category=category,
                date=date,
                amount=amount,
            )
            transaction.save()
