import pandas as pd

from statement_imports.cards.card_canonicalizer import CardCanonicalizer


class BankOfAmericaCards(CardCanonicalizer):
    """
    Class for canonicalizing Bank of America card data.
    """

    @classmethod
    def from_file(cls, card_name: str, file_path: str):
        """
        Reads Bank of America card data from a file."
        """
        df = pd.read_csv(file_path, header=0)
        return cls(card_name, df)

    @property
    def input_columns(self):
        """
        Returns the input columns for Bank of America card data.
        """
        return ["Posted Date", "Reference Number", "Payee", "Address", "Amount"]

    def _format(self):
        """
        Canonicalizes the given Bank of America card data.
        """
        pass

    def format_date(self) -> None:
        self.formatted_df["Date"] = self.df["Posted Date"]

    def format_description(self) -> None:
        self.formatted_df["Description"] = self.df["Payee"]

    def format_amount(self) -> None:
        self.formatted_df["Amount"] = self.df["Amount"]
