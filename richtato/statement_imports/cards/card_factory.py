from richtato.apps.expense.models import Expense
from richtato.statement_imports.cards.american_express import AmericanExpressCards
from richtato.statement_imports.cards.bank_of_america import BankOfAmericaCards
from richtato.statement_imports.cards.citi import CitiCards


class CardStatement:
    """
    Factory class that creates instances of card canonicalizers based on card type.

    This factory maintains a registry of available card canonicalizer classes
    and instantiates the appropriate one based on the card type argument.
    """

    _canonicalizers = {}

    @classmethod
    def register(cls, card_name, canonicalizer_class):
        """
        Register a canonicalizer class for a specific card type.

        Args:
            card_type (str): Identifier for the card type
            canonicalizer_class (class): The card canonicalizer class to register
        """
        cls._canonicalizers[card_name.lower()] = canonicalizer_class

    @classmethod
    def create_from_file(cls, user, card_type, card_name, file_path):
        """
        Create an instance of the appropriate card canonicalizer using its from_file method.

        Args:
            card_type (str): The type of card to process
            card_name (str): The name of the card
            file_path (str): Path to the file containing card data

        Returns:
            CardCanonicalizer: An instance of the appropriate canonicalizer

        Raises:
            ValueError: If no canonicalizer is registered for the given card type
        """
        card_type_lower = card_type.lower()

        if card_type_lower not in cls._canonicalizers:
            available_types = ", ".join(cls._canonicalizers.keys())
            raise ValueError(
                f"No canonicalizer registered for card type '{card_type}'. "
                f"Available types: {available_types}"
            )

        # Use the from_file class method instead of constructor
        canonicalizer_class = cls._canonicalizers[card_type_lower]
        return canonicalizer_class.from_file(user, card_name, file_path)

def register_card_canonicalizers():
    """Register all available card canonicalizer classes with the factory."""

    CardStatement.register("american_express", AmericanExpressCards)
    CardStatement.register("bank_of_america", BankOfAmericaCards)
    CardStatement.register("chase", CitiCards)


register_card_canonicalizers()
