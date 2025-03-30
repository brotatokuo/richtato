import pandas as pd

from statement_imports.cards.card_canonicalizer import CardCanonicalizer


class AmexCards(CardCanonicalizer):
    """
    Class for canonicalizing AMEX card data.
    """

    @classmethod
    def from_file(cls, card_name: str, file_path: str):
        """
        Reads AMEX card data from a file."
        """
        df = pd.read_excel(file_path, header=6, engine="openpyxl")
        return cls(card_name, df)

    @property
    def input_columns(self):
        """
        Returns the input columns for AMEX card data.
        """

        return [
            "Date",
            "Description",
            "Amount",
            "Extended Details",
            "Appears On Your Statement As",
            "Address",
            "City/State",
            "Zip Code",
            "Country",
            "Reference",
            "Category",
        ]

    def _format(self):
        """
        Canonicalizes the given AMEX card data.
        """
        pass

    def format_date(self) -> None:
        self.formatted_df["Date"] = self.df["Date"]

    def format_description(self) -> None:
        self.formatted_df["Description"] = self.df["Description"]

    def format_amount(self) -> None:
        self.formatted_df["Amount"] = self.df["Amount"]
