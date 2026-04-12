"""Management command to process categorization queue."""

from django.core.management.base import BaseCommand
from loguru import logger

from apps.categorization.models import CategorizationQueue
from apps.categorization.services.batch_ai_service import (
    BatchAICategorizationService,
)


class Command(BaseCommand):
    help = "Process pending AI categorization queue items"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of queue items to process (default: 10)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=75,
            help="Number of transactions per batch (default: 75)",
        )
        parser.add_argument(
            "--user",
            type=str,
            help="Process only for specific user (username)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Process all pending items (ignore limit)",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        batch_size = options["batch_size"]
        user_filter = options.get("user")
        process_all = options.get("all", False)

        self.stdout.write(self.style.SUCCESS(f"Starting categorization queue processing (batch_size={batch_size})"))

        # Get pending queue items
        queryset = CategorizationQueue.objects.filter(status="pending").select_related("user")

        if user_filter:
            queryset = queryset.filter(user__username=user_filter)

        if not process_all:
            queryset = queryset[:limit]

        queue_items = list(queryset)

        if not queue_items:
            self.stdout.write(self.style.WARNING("No pending queue items found"))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(queue_items)} pending queue items"))

        # Initialize service
        batch_service = BatchAICategorizationService()
        batch_service.batch_size = batch_size

        # Process each queue item
        total_processed = 0
        total_categorized = 0
        total_failed = 0

        for queue_item in queue_items:
            self.stdout.write(
                f"\nProcessing queue item {queue_item.id} "
                f"({len(queue_item.transaction_ids)} transactions) "
                f"for user {queue_item.user.username}..."
            )

            try:
                # Mark as processing
                queue_item.mark_processing()

                # Process transactions
                results = batch_service.categorize_transaction_ids(queue_item.transaction_ids, queue_item.user)

                # Update queue item
                queue_item.mark_completed(
                    categorized=results["categorized"],
                    failed=results["failed"],
                    processed=results["total"],
                )

                total_processed += results["total"]
                total_categorized += results["categorized"]
                total_failed += results["failed"]

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Queue item {queue_item.id}: "
                        f"{results['categorized']} categorized, "
                        f"{results['failed']} failed, "
                        f"{results['skipped']} skipped"
                    )
                )

            except Exception as e:
                error_msg = f"Error processing queue item {queue_item.id}: {str(e)}"
                logger.error(error_msg)
                queue_item.mark_failed(error_msg)

                self.stdout.write(self.style.ERROR(f"✗ {error_msg}"))

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'=' * 60}\n"
                f"Processing Complete!\n"
                f"{'=' * 60}\n"
                f"Queue Items Processed: {len(queue_items)}\n"
                f"Transactions Processed: {total_processed}\n"
                f"Successfully Categorized: {total_categorized}\n"
                f"Failed: {total_failed}\n"
                f"{'=' * 60}"
            )
        )
