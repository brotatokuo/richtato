from abc import ABC, abstractmethod

import pandas as pd


class CardCanonicalizer(ABC):
    """
    Abstract class for canonicalizing card data.
    """

    def __init__(self, card_name: str, df: pd.DataFrame):
        """
        Initializes the CardCanonicalizer with a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing card data.
        """
        self.card_name = card_name
        self.df = df
        self.formatted_df = pd.DataFrame()
        self.output_columns = ["Card", "Date", "Description", "Amount", "Category"]
        self.check_input_format()

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
        return self.formatted_df

    def check_input_format(self):
        """
        Checks if the input DataFrame has the required format.
        """
        if self.df.columns.tolist() != self.input_columns:
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
        self.formatted_df["Amount"] = abs(
            self.formatted_df["Amount"].astype(float).round(2)
        )
