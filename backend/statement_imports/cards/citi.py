import pandas as pd

from richtato.apps.richtato_user.models import User
from richtato.statement_imports.cards.card_canonicalizer import CardCanonicalizer


class CitiCards(CardCanonicalizer):
    """
    Class for canonicalizing CitiBank card data.
    """

    @classmethod
    def from_file(cls, user: User, card_name: str, file_path: str):
        """
        Reads CitiBank card data from a file."
        """
        df = pd.read_csv(file_path, skiprows=4, header=0)
        return cls(user, card_name, df)

    @property
    def input_columns(self):
        """
        Returns the input columns for CitiBank card data.
        """
        return ["Date", "Description", "Debit", "Credit", "Category"]

    def _format(self):
        """
        Canonicalizes the given CitiBank card data.
        """
        self.format_date()
        self.format_description()
        self.format_amount()

    def format_date(self) -> None:
        self.formatted_df["Date"] = self.df["Date"]

    def format_description(self) -> None:
        self.formatted_df["Description"] = self.df["Description"]

    def format_amount(self) -> None:
        debit = self.df["Debit"].str.replace(",", "").astype(float).fillna(0)
        credit = self.df["Credit"].str.replace(",", "").astype(float).fillna(0)
        self.formatted_df["Amount"] = debit + credit
        self.formatted_df["Amount"] = debit + credit
