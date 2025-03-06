from abc import ABC, abstractmethod

import pandas as pd


class BankImporter(ABC):
    def __init__(self, df: pd.DataFrame):
        self.df = df

    @property
    def output_columns(self):
        return ["description", "date", "amount", "account_name"]

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def _compute_description_column(self):
        """
        Computes the description column
        """

    @abstractmethod
    def _compute_date_column(self):
        """
        Computes the date column
        """

    @abstractmethod
    def _compute_amount_column(self):
        """
        Computes the amount column
        """

    def _compute_account_name_column(self):
        """
        Computes the account name column
        """
        return self.name

    def _format_description_column(self):
        """
        Formats the description column
        """
        self.df["description"] = self.df["description"].apply(self._format_description)

    def _format_date_column(self):
        """
        Formats the date column
        """
        self.df["date"] = self.df["date"].apply(self._format_date)

    def _format_amount_column(self):
        """
        Formats the amount column
        """
        self.df["amount"] = self.df["amount"].apply(self._convert_currency_to_str_float)

    @staticmethod
    def _format_description(value: str):
        """
        Formats the description column
        """
        return value[0:30].title()

    @staticmethod
    def _convert_currency_to_str_float(value: float):
        return "${:,.2f}".format(value)

    @staticmethod
    def _format_date(value: pd.Timestamp):
        """
        Formats the date column
        """
        return value.strftime("%Y-%m-%d")

    def compute_columns(self):
        """
        Computes the required output columns
        """
        self.df["description"] = self._compute_description_column()
        self.df["date"] = self._compute_date_column()
        self.df["amount"] = self._compute_amount_column()
        self.df["account_name"] = self._compute_account_name_column()
        return self.df

    def format(self):
        """
        Formats the transaction columns to a unified format
        """
        self._format_description_column()
        self._format_date_column()
        self._format_amount_column()
        return self.df
