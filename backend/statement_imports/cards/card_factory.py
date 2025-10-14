from apps.richtato_user.models import User
from statement_imports.cards.american_express import AmericanExpressCards
from statement_imports.cards.bank_of_america import BankOfAmericaCards
from statement_imports.cards.chase import ChaseCards
from statement_imports.cards.citi import CitiCards
from loguru import logger


class CardStatement:
    """
    Factory class that creates instances of card canonicalizers based on card type.

    This factory maintains a registry of available card canonicalizer classes
    and instantiates the appropriate one based on the card type argument.
    """

    _canonicalizers = {}

    @classmethod
    def register(cls, card_type, canonicalizer_class):
        """
        Register a canonicalizer class for a specific card type.

        Args:
            card_type (str): Identifier for the card type
            canonicalizer_class (class): The card canonicalizer class to register
        """
        cls._canonicalizers[card_type.lower()] = canonicalizer_class

    @classmethod
    def create_from_file(
        cls, user: User, card_bank: str, card_name: str, file_path: str
    ):
        """
        Create an instance of the appropriate card canonicalizer using its from_file method.

        Args:
            card_bank (str): The id of the card account
            card_name (str): The name of the card
            file_path (str): Path to the file containing card data

        Returns:
            CardCanonicalizer: An instance of the appropriate canonicalizer

        Raises:
            ValueError: If no canonicalizer is registered for the given card type
        """
        card_bank_lower = card_bank.lower()

        if card_bank_lower not in cls._canonicalizers:
            available_types = ", ".join(cls._canonicalizers.keys())
            raise ValueError(
                f"No canonicalizer registered for card type '{card_bank}'. "
                f"Available types: {available_types}"
            )

        # Use the from_file class method instead of constructor
        canonicalizer_class = cls._canonicalizers[card_bank_lower]
        return canonicalizer_class.from_file(user, card_name, file_path)


def register_card_canonicalizers():
    """Register all available card canonicalizer classes with the factory."""

    CardStatement.register("american_express", AmericanExpressCards)
    CardStatement.register("bank_of_america", BankOfAmericaCards)
    CardStatement.register("citibank", CitiCards)
    CardStatement.register("chase", ChaseCards)


register_card_canonicalizers()
