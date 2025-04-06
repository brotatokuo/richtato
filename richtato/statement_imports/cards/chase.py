import pandas as pd

from richtato.apps.richtato_user.models import User
from richtato.statement_imports.cards.card_canonicalizer import CardCanonicalizer


class ChaseCards(CardCanonicalizer):
    """
    Class for canonicalizing Chase card data.
    """

    @classmethod
    def from_file(cls, user: User, card_name: str, file_path: str):
        """
        Reads Chase card data from a file."
        """
        df = pd.read_csv(file_path, header=0)
        return cls(user, card_name, df)

    @property
    def input_columns(self):
        """
        Returns the input columns for Chase card data.
        """
        return [
            "Transaction Date",
            "Post Date",
            "Description",
            "Category",
            "Type",
            "Amount",
            "Memo",
        ]

    def _format(self):
        """
        Canonicalizes the given Chase card data.
        """
        print(self.df.columns)
        self.format_date()
        self.format_description()
        self.format_amount()

    def format_date(self) -> None:
        self.formatted_df["Date"] = self.df["Transaction Date"]

    def format_description(self) -> None:
        self.formatted_df["Description"] = self.df["Description"]

    def format_amount(self) -> None:
        self.formatted_df["Amount"] = self.df["Amount"].astype(float)
