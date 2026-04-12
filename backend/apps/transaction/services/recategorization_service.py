"""Service for bulk recategorization of transactions."""

from collections.abc import Callable

from django.utils import timezone
from loguru import logger

from apps.transaction.models import RecategorizationTask, Transaction
from apps.transaction.services.transaction_service import TransactionService


class RecategorizationService:
    """Service for bulk recategorization of user transactions."""

    def __init__(self):
        self.transaction_service = TransactionService()

    def recategorize_all_transactions(
        self,
        task: RecategorizationTask,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, int]:
        """
        Recategorize all transactions for a user based on their current keywords.

        Args:
            task: RecategorizationTask instance to track progress
            progress_callback: Optional callback for progress updates (processed, total)

        Returns:
            Dict with statistics: {
                'total': int,
                'processed': int,
                'updated': int,
                'unchanged': int,
                'unmatched': int
            }
        """
        user = task.user
        keep_existing = task.keep_existing_for_unmatched

        # Update task status to processing
        task.status = "processing"
        task.save(update_fields=["status"])

        try:
            # Get only uncategorized transactions for the user
            # This protects manually-categorized transactions from being overwritten
            transactions = Transaction.objects.filter(
                user=user,
                categorization_status="uncategorized",
            ).select_related("category")
            total_count = transactions.count()

            # Update task with total count
            task.total_count = total_count
            task.save(update_fields=["total_count"])

            logger.info(f"Starting recategorization for user {user.id}: {total_count} transactions")

            # Statistics
            stats = {
                "total": total_count,
                "processed": 0,
                "updated": 0,
                "unchanged": 0,
                "unmatched": 0,
            }

            # Process transactions in batches to avoid memory issues
            batch_size = 100
            for i in range(0, total_count, batch_size):
                batch = transactions[i : i + batch_size]

                for txn in batch:
                    old_category = txn.category
                    old_category_id = old_category.id if old_category else None

                    # Try to match category via keywords
                    new_category = self.transaction_service._match_category_via_keywords(user, txn.description)

                    if new_category:
                        # Found a keyword match
                        new_category_id = new_category.id
                        if old_category_id != new_category_id:
                            txn.category = new_category
                            txn.categorization_status = "categorized"
                            txn.save(update_fields=["category", "categorization_status"])
                            stats["updated"] += 1
                        else:
                            stats["unchanged"] += 1
                    else:
                        # No keyword match found
                        stats["unmatched"] += 1
                        if not keep_existing:
                            # User wants to mark unmatched as uncategorized
                            if old_category_id is not None:
                                txn.category = None
                                txn.categorization_status = "uncategorized"
                                txn.save(update_fields=["category", "categorization_status"])
                                stats["updated"] += 1
                            else:
                                stats["unchanged"] += 1
                        else:
                            # Keep existing category
                            stats["unchanged"] += 1

                    stats["processed"] += 1

                    # Update task progress
                    if stats["processed"] % 10 == 0:  # Update every 10 transactions
                        task.processed_count = stats["processed"]
                        task.updated_count = stats["updated"]
                        task.save(update_fields=["processed_count", "updated_count"])

                        if progress_callback:
                            progress_callback(stats["processed"], total_count)

            # Mark task as completed
            task.status = "completed"
            task.processed_count = stats["processed"]
            task.updated_count = stats["updated"]
            task.completed_at = timezone.now()
            task.save(
                update_fields=[
                    "status",
                    "processed_count",
                    "updated_count",
                    "completed_at",
                ]
            )

            logger.info(
                f"Recategorization completed for user {user.id}: "
                f"{stats['updated']} updated, {stats['unchanged']} unchanged, "
                f"{stats['unmatched']} unmatched"
            )

            return stats

        except Exception as e:
            # Mark task as failed
            logger.error(f"Recategorization failed for user {user.id}: {str(e)}")
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save(update_fields=["status", "error_message", "completed_at"])
            raise
