import re
from abc import ABC, abstractmethod
from decimal import Decimal

import pandas as pd
from apps.financial_account.models import FinancialAccount
from apps.transaction.models import Transaction, TransactionCategory
from apps.transaction.services.transaction_service import TransactionService
from artificial_intelligence.ai import OpenAI
from loguru import logger


class CardCanonicalizer(ABC):
    """
    Abstract class for canonicalizing card data.
    """

    def __init__(self, user, card_name: str, df: pd.DataFrame):
        """
        Initializes the CardCanonicalizer with a DataFrame.

        Args:
            user: User instance
            card_name: Name of the card/account
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
        self.drop_payment_rows()
        self._convert_date()
        self._convert_amount()
        self._compute_category()
        self.formatted_df.sort_values("Date", inplace=True)
        self.formatted_df.reset_index(drop=True, inplace=True)
        return self.formatted_df

    def drop_payment_rows(self) -> None:
        """
        Drops rows that are not needed
        """
        keywords_to_filter = [
            "Online payment",
            "Mobile payment",
            # Add more as needed
        ]

        # Join the keywords into a regex pattern
        pattern = "|".join(
            map(re.escape, keywords_to_filter)
        )  # escape handles special characters

        # Filter the DataFrame
        self.df = self.df[
            ~self.df["Description"].str.contains(pattern, case=False, na=False)
        ]

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
        transaction_service = TransactionService()

        def match_category(description: str) -> str:
            """Match category via keywords and return category name or None."""
            category = transaction_service._match_category_via_keywords(
                self.user, description
            )
            return category.name if category else None

        self.formatted_df["Category"] = self.formatted_df["Description"].apply(
            match_category
        )
        uncategorized_mask = self.formatted_df["Category"].isna()
        logger.debug(
            f"Uncategorized transactions: {self.formatted_df[uncategorized_mask].to_string()}"
        )

        uncategorized_df = self.formatted_df[uncategorized_mask]
        categorized_df = OpenAI().categorize_dataframe(self.user, uncategorized_df)
        self.formatted_df.loc[uncategorized_mask, "Category"] = categorized_df[
            "Category"
        ].values

    def process(self) -> None:
        """
        Iterate through card's formatted df and add each to the database.
        """

        card_name = self.formatted_df["Card"].unique().tolist()[0]
        for _, row in self.formatted_df.iterrows():
            description = row["Description"]
            category_name = row["Category"]
            date = row["Date"]
            amount = row["Amount"]

            # Get or create the financial account
            account = FinancialAccount.objects.filter(
                name=card_name, user=self.user
            ).first()

            if not account:
                # Create the account if it doesn't exist
                account = FinancialAccount.objects.create(
                    user=self.user,
                    name=card_name,
                    account_type="credit_card",
                    sync_source="csv",
                )

            try:
                # Get or create the category
                category, _ = TransactionCategory.objects.get_or_create(
                    name=category_name,
                    user=self.user,
                    defaults={
                        "slug": category_name.lower()
                        .replace(" ", "-")
                        .replace("/", "-"),
                        "is_expense": True,
                    },
                )

                # Create the transaction
                transaction = Transaction(
                    user=self.user,
                    account=account,
                    description=description,
                    category=category,
                    date=date,
                    amount=Decimal(str(amount)),
                    transaction_type="debit",
                    sync_source="csv",
                )
                transaction.save()
            except TransactionCategory.DoesNotExist:
                available_categories = TransactionCategory.objects.filter(
                    user=self.user
                ).values_list("name", flat=True)
                logger.error(
                    f"Category '{category_name}' does not exist. Available categories: {list(available_categories)}"
                )
                break
