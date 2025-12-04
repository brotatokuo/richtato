"""Refactored Teller sync service using new unified architecture."""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List

from apps.categorization.models import CategorizationQueue
from apps.categorization.services.batch_ai_service import (
    BatchAICategorizationService,
)
from apps.categorization.services.rule_based_service import (
    RuleBasedCategorizationService,
)
from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.richtato_user.models import User
from apps.sync.models import SyncConnection, SyncJob
from apps.sync.repositories.sync_job_repository import SyncJobRepository
from apps.transaction.repositories.merchant_repository import MerchantRepository
from apps.transaction.repositories.transaction_repository import TransactionRepository
from django.conf import settings
from integrations.teller.client import TellerClient
from loguru import logger


class TellerSyncService:
    """Refactored service for syncing Teller data to unified transaction model."""

    def __init__(self):
        self.account_repository = FinancialAccountRepository()
        self.transaction_repository = TransactionRepository()
        self.merchant_repository = MerchantRepository()
        self.job_repository = SyncJobRepository()
        self.rule_categorization = RuleBasedCategorizationService()
        self.batch_ai_categorization = BatchAICategorizationService()

    def _get_teller_client(self, connection: SyncConnection) -> TellerClient:
        """Create a TellerClient instance for the connection."""
        cert_path = settings.TELLER_CERT_PATH
        key_path = settings.TELLER_KEY_PATH

        if not cert_path or not key_path:
            raise ValueError("Teller certificate paths not configured in settings")

        return TellerClient(
            cert_path=cert_path,
            key_path=key_path,
            access_token=connection.access_token,
        )

    def sync_connection(
        self, connection: SyncConnection, force_full_sync: bool = False
    ) -> Dict:
        """
        Sync transactions from Teller for a specific connection.

        On first sync (when initial_backfill_complete is False), this will
        automatically trigger a full historical sync.

        Args:
            connection: SyncConnection to sync
            force_full_sync: If True, perform full historical sync regardless

        Returns:
            Dict with sync results
        """
        # Check if this is first sync or forced full sync
        is_full_sync = not connection.initial_backfill_complete or force_full_sync

        if is_full_sync:
            logger.info(
                f"Triggering full historical sync for connection {connection.id}"
            )
            return self.sync_historical_transactions(connection)
        else:
            logger.info(f"Triggering incremental sync for connection {connection.id}")
            return self.sync_recent_transactions(connection)

    def sync_historical_transactions(self, connection: SyncConnection) -> Dict:
        """
        Sync all available historical transactions from Teller using pagination.

        Args:
            connection: SyncConnection to sync

        Returns:
            Dict with sync results
        """
        # Create sync job
        job = self.job_repository.create_job(connection, is_full_sync=True)

        results = {
            "success": False,
            "transactions_synced": 0,
            "transactions_skipped": 0,
            "batches_processed": 0,
            "errors": [],
            "message": "",
        }

        try:
            client = self._get_teller_client(connection)
            user = connection.user
            account = connection.account

            # Track oldest transaction date
            oldest_date = None
            total_synced = 0
            total_skipped = 0
            pending_ai_categorization = (
                []
            )  # Track transactions needing AI categorization

            logger.info(
                f"Starting historical sync for connection {connection.id} "
                f"(account: {connection.external_account_id})"
            )

            # Fetch transactions in batches using pagination
            batch_size = getattr(settings, "TELLER_TRANSACTION_LIMIT", 500)
            for batch in client.get_transactions_paginated(
                account_id=connection.external_account_id,
                batch_size=batch_size,
            ):
                results["batches_processed"] += 1
                batch_synced = 0
                batch_skipped = 0

                logger.info(
                    f"Processing batch {results['batches_processed']} "
                    f"with {len(batch)} transactions"
                )

                for txn in batch:
                    try:
                        # Parse transaction data
                        txn_date = datetime.strptime(txn["date"], "%Y-%m-%d").date()
                        txn_amount_raw = Decimal(str(txn["amount"]))
                        txn_amount = abs(txn_amount_raw)
                        txn_description = txn.get("description", "")
                        txn_id = txn.get("id", "")

                        # Track oldest date
                        if oldest_date is None or txn_date < oldest_date:
                            oldest_date = txn_date

                        # Check if already exists by external_id
                        existing = self.transaction_repository.get_by_external_id(
                            user, txn_id, "teller"
                        )
                        if existing:
                            batch_skipped += 1
                            continue

                        # Determine transaction type based on account type
                        # For credit cards: positive = purchase (expense), negative = payment/refund
                        # For bank accounts: positive = deposit (income), negative = withdrawal (expense)
                        if account.account_type == "credit_card":
                            transaction_type = (
                                "debit" if txn_amount_raw > 0 else "credit"
                            )
                        else:
                            transaction_type = (
                                "credit" if txn_amount_raw > 0 else "debit"
                            )

                        # Get or create merchant if available
                        merchant = None
                        merchant_name = (
                            txn.get("merchant", {}).get("name")
                            if isinstance(txn.get("merchant"), dict)
                            else None
                        )
                        if merchant_name:
                            merchant = self.merchant_repository.get_or_create_merchant(
                                name=merchant_name
                            )

                        # Create transaction
                        transaction = self.transaction_repository.create_transaction(
                            user=user,
                            account=account,
                            date=txn_date,
                            amount=txn_amount,
                            description=txn_description,
                            transaction_type=transaction_type,
                            merchant=merchant,
                            status="posted",
                            sync_source="teller",
                            external_id=txn_id,
                            raw_data=txn,
                        )

                        # Try rule-based categorization (fast)
                        if not self._auto_categorize_transaction(transaction):
                            # If not categorized by rules, mark for AI processing
                            transaction.categorization_status = "pending_ai"
                            transaction.save()
                            pending_ai_categorization.append(transaction.id)

                        batch_synced += 1
                        total_synced += 1

                    except Exception as e:
                        logger.error(
                            f"Error syncing transaction {txn.get('id')}: {str(e)}"
                        )
                        results["errors"].append(str(e))
                        continue

                total_skipped += batch_skipped

                logger.info(
                    f"Batch {results['batches_processed']}: "
                    f"synced {batch_synced}, skipped {batch_skipped}"
                )

                # Update job progress
                job.transactions_synced = total_synced
                job.transactions_skipped = total_skipped
                job.batches_processed = results["batches_processed"]
                job.save()

            results["transactions_synced"] = total_synced
            results["transactions_skipped"] = total_skipped
            results["pending_ai_categorization"] = len(pending_ai_categorization)

            # Queue uncategorized transactions for batch AI processing
            if pending_ai_categorization:
                self._queue_for_ai_categorization(pending_ai_categorization, user)
                logger.info(
                    f"Queued {len(pending_ai_categorization)} transactions "
                    f"for AI categorization"
                )

            # Mark connection as successfully synced
            connection.mark_synced(backfill_complete=True, oldest_date=oldest_date)

            # Mark job as completed
            job.mark_completed(total_synced, total_skipped)

            results["success"] = True
            results["message"] = (
                f"Successfully synced {total_synced} transactions, "
                f"skipped {total_skipped} duplicates across "
                f"{results['batches_processed']} batches. "
                f"Oldest transaction: {oldest_date if oldest_date else 'N/A'}. "
                f"{len(pending_ai_categorization)} queued for AI categorization."
            )

            logger.info(results["message"])

        except Exception as e:
            error_msg = f"Error syncing historical transactions: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["message"] = error_msg
            connection.mark_error(error_msg)
            job.mark_failed(error_msg)

        return results

    def sync_recent_transactions(
        self, connection: SyncConnection, days: int = 30
    ) -> Dict:
        """
        Sync recent transactions (last N days) for incremental updates.

        Args:
            connection: SyncConnection to sync
            days: Number of days to fetch (default 30)

        Returns:
            Dict with sync results
        """
        # Create sync job
        job = self.job_repository.create_job(connection, is_full_sync=False)

        results = {
            "success": False,
            "transactions_synced": 0,
            "transactions_skipped": 0,
            "errors": [],
            "message": "",
        }

        try:
            client = self._get_teller_client(connection)
            user = connection.user
            account = connection.account
            pending_ai_categorization = []  # Track transactions needing AI

            # Fetch recent transactions
            transaction_limit = min(
                getattr(settings, "TELLER_TRANSACTION_LIMIT", 500), 100
            )
            transactions = client.get_transactions(
                connection.external_account_id, count=transaction_limit
            )

            logger.info(
                f"Fetched {len(transactions)} recent transactions for "
                f"connection {connection.id}"
            )

            synced_count = 0
            skipped_count = 0

            for txn in transactions:
                try:
                    txn_date = datetime.strptime(txn["date"], "%Y-%m-%d").date()
                    txn_amount_raw = Decimal(str(txn["amount"]))
                    txn_amount = abs(txn_amount_raw)
                    txn_description = txn.get("description", "")
                    txn_id = txn.get("id", "")

                    # Check if already exists
                    existing = self.transaction_repository.get_by_external_id(
                        user, txn_id, "teller"
                    )
                    if existing:
                        skipped_count += 1
                        continue

                    # Determine transaction type based on account type
                    # For credit cards: positive = purchase (expense), negative = payment/refund
                    # For bank accounts: positive = deposit (income), negative = withdrawal (expense)
                    if account.account_type == "credit_card":
                        transaction_type = "debit" if txn_amount_raw > 0 else "credit"
                    else:
                        transaction_type = "credit" if txn_amount_raw > 0 else "debit"

                    # Get or create merchant
                    merchant = None
                    merchant_name = (
                        txn.get("merchant", {}).get("name")
                        if isinstance(txn.get("merchant"), dict)
                        else None
                    )
                    if merchant_name:
                        merchant = self.merchant_repository.get_or_create_merchant(
                            name=merchant_name
                        )

                    # Create transaction
                    transaction = self.transaction_repository.create_transaction(
                        user=user,
                        account=account,
                        date=txn_date,
                        amount=txn_amount,
                        description=txn_description,
                        transaction_type=transaction_type,
                        merchant=merchant,
                        status="posted",
                        sync_source="teller",
                        external_id=txn_id,
                        raw_data=txn,
                    )

                    # Try rule-based categorization (fast)
                    if not self._auto_categorize_transaction(transaction):
                        # If not categorized by rules, mark for AI processing
                        transaction.categorization_status = "pending_ai"
                        transaction.save()
                        pending_ai_categorization.append(transaction.id)

                    synced_count += 1

                except Exception as e:
                    logger.error(f"Error syncing transaction {txn.get('id')}: {str(e)}")
                    results["errors"].append(str(e))
                    continue

            results["transactions_synced"] = synced_count
            results["transactions_skipped"] = skipped_count
            results["pending_ai_categorization"] = len(pending_ai_categorization)

            # Queue uncategorized transactions for batch AI processing
            if pending_ai_categorization:
                self._queue_for_ai_categorization(pending_ai_categorization, user)
                logger.info(
                    f"Queued {len(pending_ai_categorization)} transactions "
                    f"for AI categorization"
                )

            # Mark connection as synced
            connection.mark_synced()

            # Mark job as completed
            job.mark_completed(synced_count, skipped_count)

            results["success"] = True
            results["message"] = (
                f"Successfully synced {synced_count} new transactions, "
                f"skipped {skipped_count} duplicates. "
                f"{len(pending_ai_categorization)} queued for AI categorization."
            )

            logger.info(results["message"])

        except Exception as e:
            error_msg = f"Error syncing recent transactions: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["message"] = error_msg
            connection.mark_error(error_msg)
            job.mark_failed(error_msg)

        return results

    def _auto_categorize_transaction(self, transaction) -> bool:
        """
        Attempt rule-based categorization during sync (fast path).

        Args:
            transaction: Transaction to categorize

        Returns:
            True if categorized, False if needs AI categorization
        """
        try:
            # Try rule-based categorization (< 1ms)
            rule_result = self.rule_categorization.categorize_transaction(transaction)
            if rule_result:
                category, rule = rule_result
                self.rule_categorization.apply_categorization(
                    transaction, category, rule
                )
                # Mark as categorized
                transaction.categorization_status = "categorized"
                transaction.save()
                return True

            # No rule match - needs AI categorization
            return False

        except Exception as e:
            logger.error(f"Error in rule-based categorization: {str(e)}")
            return False

    def _queue_for_ai_categorization(
        self, transaction_ids: List[int], user: User
    ) -> CategorizationQueue:
        """
        Queue transactions for batch AI categorization.

        Args:
            transaction_ids: List of transaction IDs to categorize
            user: User who owns the transactions

        Returns:
            Created CategorizationQueue instance
        """
        queue_item = CategorizationQueue.objects.create(
            user=user,
            transaction_ids=transaction_ids,
            status="pending",
        )

        logger.info(
            f"Created categorization queue item {queue_item.id} "
            f"with {len(transaction_ids)} transactions for user {user.username}"
        )

        return queue_item
