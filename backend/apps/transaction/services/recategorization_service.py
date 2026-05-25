"""Service for bulk recategorization of transactions."""

from collections.abc import Callable

from django.utils import timezone
from loguru import logger

from apps.transaction.models import RecategorizationTask, Transaction, TransactionCategory
from apps.transaction.services.keyword_matching import load_user_keywords, match_category_from_keywords


class RecategorizationService:
    """Service for bulk recategorization of user transactions."""

    BATCH_SIZE = 500
    PROGRESS_INTERVAL = 50

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

        task.status = "processing"
        task.save(update_fields=["status"])

        try:
            keywords = load_user_keywords(user)
            uncategorized_category = None
            if not keep_existing:
                uncategorized_category = TransactionCategory.get_uncategorized_for_user(user)

            transactions = Transaction.objects.filter(
                user=user,
                categorization_status="uncategorized",
            )
            total_count = transactions.count()

            task.total_count = total_count
            task.save(update_fields=["total_count"])

            logger.info(f"Starting recategorization for user {user.id}: {total_count} transactions")

            stats = {
                "total": total_count,
                "processed": 0,
                "updated": 0,
                "unchanged": 0,
                "unmatched": 0,
            }

            pending_updates: list[Transaction] = []

            for txn in transactions.iterator(chunk_size=self.BATCH_SIZE):
                old_category_id = txn.category_id
                new_category = match_category_from_keywords(txn.description, keywords)

                if new_category:
                    if old_category_id != new_category.id:
                        txn.category_id = new_category.id
                        txn.categorization_status = "categorized"
                        pending_updates.append(txn)
                        stats["updated"] += 1
                    else:
                        stats["unchanged"] += 1
                else:
                    stats["unmatched"] += 1
                    if not keep_existing and old_category_id is not None and uncategorized_category:
                        if old_category_id != uncategorized_category.id:
                            txn.category_id = uncategorized_category.id
                            txn.categorization_status = "uncategorized"
                            pending_updates.append(txn)
                            stats["updated"] += 1
                        else:
                            stats["unchanged"] += 1
                    else:
                        stats["unchanged"] += 1

                stats["processed"] += 1

                if len(pending_updates) >= self.BATCH_SIZE:
                    self._bulk_update_categories(pending_updates)
                    pending_updates = []

                if stats["processed"] % self.PROGRESS_INTERVAL == 0:
                    self._update_task_progress(task, stats)
                    if progress_callback:
                        progress_callback(stats["processed"], total_count)

            if pending_updates:
                self._bulk_update_categories(pending_updates)

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
            logger.error(f"Recategorization failed for user {user.id}: {str(e)}")
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save(update_fields=["status", "error_message", "completed_at"])
            raise

    def _bulk_update_categories(self, transactions: list[Transaction]) -> None:
        """Persist category changes without per-row save/signal overhead."""
        Transaction.objects.bulk_update(
            transactions,
            ["category_id", "categorization_status"],
            batch_size=self.BATCH_SIZE,
        )

    def _update_task_progress(self, task: RecategorizationTask, stats: dict[str, int]) -> None:
        task.processed_count = stats["processed"]
        task.updated_count = stats["updated"]
        task.save(update_fields=["processed_count", "updated_count"])
