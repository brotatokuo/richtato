"""AI-based categorization service using OpenAI."""

from decimal import Decimal

from loguru import logger

from apps.categorization.models import CategorizationHistory
from apps.transaction.models import Transaction, TransactionCategory
from apps.transaction.repositories.category_repository import CategoryRepository
from artificial_intelligence.ai import OpenAI


class AICategorizationService:
    """Service for AI-based transaction categorization using OpenAI."""

    def __init__(self):
        self.ai = OpenAI()
        self.category_repository = CategoryRepository()

    def suggest_category(
        self,
        transaction: Transaction,
        available_categories: list[TransactionCategory] = None,
    ) -> tuple[TransactionCategory, Decimal] | None:
        """
        Suggest a category for a transaction using AI.

        Args:
            transaction: Transaction to categorize
            available_categories: Optional list of categories to choose from

        Returns:
            Tuple of (category, confidence_score) if successful, None otherwise
        """
        try:
            # Get available categories
            if available_categories is None:
                available_categories = self.category_repository.get_all_for_user(transaction.user, include_global=True)

            if not available_categories:
                logger.warning("No categories available for AI categorization")
                return None

            # Build prompt for AI
            prompt = self._build_categorization_prompt(transaction, available_categories)

            # Get AI suggestion
            response = self.ai.one_shot_prompt(prompt)

            # Parse response
            category, confidence = self._parse_ai_response(response, available_categories)

            if category:
                logger.info(
                    f"AI suggested category for transaction {transaction.id}: "
                    f"{category.name} (confidence: {confidence}%)"
                )
                return (category, confidence)

            return None

        except Exception as e:
            logger.error(f"Error getting AI category suggestion: {str(e)}")
            return None

    def categorize_transaction(
        self, transaction: Transaction, auto_apply: bool = False
    ) -> tuple[TransactionCategory, Decimal] | None:
        """
        Categorize a transaction using AI and optionally apply it.

        Args:
            transaction: Transaction to categorize
            auto_apply: Whether to automatically apply the suggestion

        Returns:
            Tuple of (category, confidence_score) if successful, None otherwise
        """
        result = self.suggest_category(transaction)

        if result and auto_apply:
            category, confidence = result
            transaction.category = category
            transaction.save()

            # Record in history
            CategorizationHistory.objects.create(
                transaction=transaction,
                category=category,
                method="ai",
                confidence_score=confidence,
            )

            logger.info(f"AI categorized transaction {transaction.id}: {category.name}")

        return result

    def _build_categorization_prompt(self, transaction: Transaction, categories: list[TransactionCategory]) -> str:
        """
        Build a prompt for AI categorization.

        Args:
            transaction: Transaction to categorize
            categories: Available categories

        Returns:
            Formatted prompt string
        """
        # Build category list
        category_list = []
        for cat in categories:
            if cat.parent:
                category_list.append(f"- {cat.parent.name} > {cat.name}")
            else:
                category_list.append(f"- {cat.name}")

        category_str = "\n".join(category_list)

        # Build transaction description
        merchant_info = f"\nMerchant: {transaction.merchant.name}" if transaction.merchant else ""

        prompt = f"""You are a financial transaction categorization assistant.
Analyze the following transaction and suggest the most appropriate category from the list provided.

Transaction Details:
- Description: {transaction.description}
- Amount: ${transaction.amount}
- Date: {transaction.date}
- Type: {transaction.get_transaction_type_display()}{merchant_info}

Available Categories:
{category_str}

Please respond in the following JSON format:
{{
  "category": "category_name",
  "confidence": 85,
  "reasoning": "Brief explanation"
}}

Only return the JSON, no additional text."""

        return prompt

    def _parse_ai_response(
        self, response: str, categories: list[TransactionCategory]
    ) -> tuple[TransactionCategory | None, Decimal]:
        """
        Parse AI response and match to a category.

        Args:
            response: AI response string
            categories: Available categories

        Returns:
            Tuple of (category, confidence_score)
        """
        try:
            import json

            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()

            data = json.loads(response)

            category_name = data.get("category", "").lower()
            confidence = Decimal(str(data.get("confidence", 0)))

            # Find matching category
            for cat in categories:
                if cat.name.lower() == category_name:
                    return (cat, confidence)
                # Also check full path for subcategories
                if cat.full_path.lower() == category_name:
                    return (cat, confidence)

            logger.warning(f"AI suggested unknown category: {category_name}")
            return (None, Decimal("0"))

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return (None, Decimal("0"))
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return (None, Decimal("0"))

    def batch_categorize(
        self, transactions: list[Transaction], auto_apply: bool = False
    ) -> list[tuple[Transaction, TransactionCategory | None, Decimal]]:
        """
        Categorize multiple transactions in batch.

        Args:
            transactions: List of transactions to categorize
            auto_apply: Whether to automatically apply suggestions

        Returns:
            List of tuples (transaction, category, confidence)
        """
        results = []

        for transaction in transactions:
            result = self.categorize_transaction(transaction, auto_apply=auto_apply)
            if result:
                category, confidence = result
                results.append((transaction, category, confidence))
            else:
                results.append((transaction, None, Decimal("0")))

        return results
