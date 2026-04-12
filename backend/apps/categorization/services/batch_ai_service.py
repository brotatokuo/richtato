"""Batch AI categorization service for efficient processing."""

import json
from decimal import Decimal
from typing import Dict, List, Tuple

from apps.categorization.models import CategorizationHistory
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory
from apps.transaction.repositories.category_repository import CategoryRepository
from apps.transaction.repositories.transaction_repository import TransactionRepository
from artificial_intelligence.ai import OpenAI
from loguru import logger


class BatchAICategorizationService:
    """Service for batch processing multiple transactions with AI efficiently."""

    def __init__(self):
        self.ai = OpenAI()
        self.category_repository = CategoryRepository()
        self.transaction_repository = TransactionRepository()
        self.batch_size = 75  # Medium batch size for optimal performance

    def categorize_transaction_ids(
        self, transaction_ids: List[int], user: User
    ) -> Dict:
        """
        Categorize a list of transaction IDs in batches.

        Args:
            transaction_ids: List of transaction IDs to categorize
            user: User who owns the transactions

        Returns:
            Dict with results
        """
        results = {
            "total": len(transaction_ids),
            "categorized": 0,
            "failed": 0,
            "skipped": 0,
        }

        transactions = list(
            Transaction.objects.filter(
                id__in=transaction_ids, user=user
            ).select_related("category")
        )

        if not transactions:
            logger.warning("No valid transactions found for categorization")
            return results

        # Get available categories
        categories = self.category_repository.get_all_for_user(
            user, include_global=True
        )

        if not categories:
            logger.warning("No categories available for AI categorization")
            return results

        # Process in batches
        for i in range(0, len(transactions), self.batch_size):
            batch = transactions[i : i + self.batch_size]
            batch_results = self._categorize_batch(batch, categories, user)

            results["categorized"] += batch_results["categorized"]
            results["failed"] += batch_results["failed"]
            results["skipped"] += batch_results["skipped"]

        logger.info(
            f"Batch categorization complete: {results['categorized']} categorized, "
            f"{results['failed']} failed, {results['skipped']} skipped"
        )

        return results

    def _categorize_batch(
        self,
        transactions: List[Transaction],
        categories: List[TransactionCategory],
        user: User,
    ) -> Dict:
        """
        Categorize a single batch of transactions.

        Args:
            transactions: List of transactions to categorize
            categories: Available categories
            user: User

        Returns:
            Dict with batch results
        """
        results = {"categorized": 0, "failed": 0, "skipped": 0}

        try:
            # Build batch prompt
            prompt = self._build_batch_prompt(transactions, categories)

            # Get AI response
            response = self.ai.one_shot_prompt(prompt)

            # Parse batch response
            categorizations = self._parse_batch_response(
                response, transactions, categories
            )

            # Apply categorizations
            for txn_id, category, confidence in categorizations:
                try:
                    transaction = next(
                        (t for t in transactions if t.id == txn_id), None
                    )
                    if transaction:
                        transaction.category = category
                        transaction.categorization_status = "categorized"
                        transaction.save()

                        # Record in history
                        CategorizationHistory.objects.create(
                            transaction=transaction,
                            category=category,
                            method="ai",
                            confidence_score=confidence,
                        )

                        results["categorized"] += 1
                        logger.debug(
                            f"AI categorized transaction {txn_id}: {category.name} "
                            f"(confidence: {confidence}%)"
                        )
                except Exception as e:
                    logger.error(
                        f"Error applying categorization for transaction {txn_id}: {str(e)}"
                    )
                    results["failed"] += 1

            # Mark any uncategorized transactions that AI didn't categorize
            for transaction in transactions:
                if transaction.categorization_status == "pending_ai":
                    transaction.categorization_status = "uncategorized"
                    transaction.save()
                    results["skipped"] += 1

        except Exception as e:
            logger.error(f"Error in batch AI categorization: {str(e)}")
            # Mark all transactions as uncategorized (remove pending status)
            for transaction in transactions:
                if transaction.categorization_status == "pending_ai":
                    transaction.categorization_status = "uncategorized"
                    transaction.save()
            results["failed"] = len(transactions)

        return results

    def _build_batch_prompt(
        self, transactions: List[Transaction], categories: List[TransactionCategory]
    ) -> str:
        """
        Build an efficient batch prompt for multiple transactions.

        Args:
            transactions: List of transactions
            categories: Available categories

        Returns:
            Formatted prompt string
        """
        # Build category list (simplified for token efficiency)
        category_names = []
        for cat in categories:
            if cat.parent:
                category_names.append(f"{cat.parent.name} > {cat.name}")
            else:
                category_names.append(cat.name)

        # Build transaction list
        transaction_list = []
        for idx, txn in enumerate(transactions, 1):
            merchant_info = f" | Merchant: {txn.merchant.name}" if txn.merchant else ""
            transaction_list.append(
                f'{idx}. ID:{txn.id} | "{txn.description}" | ${txn.amount} | {txn.date}{merchant_info}'
            )

        prompt = f"""You are a financial transaction categorization assistant. Categorize these {len(transactions)} transactions into the most appropriate categories.

Available Categories:
{', '.join(category_names)}

Transactions to Categorize:
{chr(10).join(transaction_list)}

Respond with ONLY a JSON array, no additional text:
[
  {{"id": {transactions[0].id}, "category": "Category Name", "confidence": 85}},
  ...
]

Rules:
- Use exact category names from the list
- Confidence: 0-100 (higher = more certain)
- Include all {len(transactions)} transactions
- Match transaction ID exactly"""

        return prompt

    def _parse_batch_response(
        self,
        response: str,
        transactions: List[Transaction],
        categories: List[TransactionCategory],
    ) -> List[Tuple[int, TransactionCategory, Decimal]]:
        """
        Parse AI batch response and match to transactions/categories.

        Args:
            response: AI response string
            transactions: Original transactions
            categories: Available categories

        Returns:
            List of tuples (transaction_id, category, confidence_score)
        """
        categorizations = []

        try:
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()
            elif response.startswith("```"):
                response = response.replace("```", "").strip()

            # Parse JSON
            data = json.loads(response)

            if not isinstance(data, list):
                logger.error("AI response is not a JSON array")
                return categorizations

            # Build category lookup for fast matching
            category_lookup = {}
            for cat in categories:
                category_lookup[cat.name.lower()] = cat
                category_lookup[cat.full_path.lower()] = cat

            # Process each categorization
            for item in data:
                try:
                    txn_id = int(item.get("id", 0))
                    category_name = item.get("category", "").lower()
                    confidence = Decimal(str(item.get("confidence", 0)))

                    # Find matching category
                    category = category_lookup.get(category_name)

                    if category and txn_id:
                        categorizations.append((txn_id, category, confidence))
                    else:
                        logger.warning(
                            f"Could not match transaction {txn_id} to category '{category_name}'"
                        )

                except Exception as e:
                    logger.error(f"Error parsing categorization item: {str(e)}")
                    continue

            logger.info(
                f"Successfully parsed {len(categorizations)} categorizations "
                f"from AI response"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI batch response as JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing batch response: {str(e)}")

        return categorizations

    def process_pending_transactions(self, user: User, limit: int = 500) -> Dict:
        """
        Process all transactions with pending_ai status for a user.

        Args:
            user: User
            limit: Maximum number of transactions to process

        Returns:
            Dict with results
        """
        # Get transactions with pending_ai status
        pending_transactions = list(
            Transaction.objects.filter(
                user=user, categorization_status="pending_ai"
            ).select_related("merchant")[:limit]
        )

        if not pending_transactions:
            logger.info(f"No pending transactions for user {user.username}")
            return {"total": 0, "categorized": 0, "failed": 0, "skipped": 0}

        logger.info(
            f"Processing {len(pending_transactions)} pending transactions "
            f"for user {user.username}"
        )

        # Get categories
        categories = self.category_repository.get_all_for_user(
            user, include_global=True
        )

        results = {
            "total": len(pending_transactions),
            "categorized": 0,
            "failed": 0,
            "skipped": 0,
        }

        # Process in batches
        for i in range(0, len(pending_transactions), self.batch_size):
            batch = pending_transactions[i : i + self.batch_size]
            batch_results = self._categorize_batch(batch, categories, user)

            results["categorized"] += batch_results["categorized"]
            results["failed"] += batch_results["failed"]
            results["skipped"] += batch_results["skipped"]

        return results
