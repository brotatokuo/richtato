"""Refactored Teller sync service using new unified architecture."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple

from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.sync.models import SyncConnection
from apps.sync.repositories.sync_job_repository import SyncJobRepository
from apps.transaction.models import CategoryKeyword, TransactionCategory
from apps.transaction.repositories.transaction_repository import TransactionRepository
from django.conf import settings
from django.db.models import Q
from integrations.teller.client import TellerClient
from loguru import logger

# Canonical slug for Credit Card Payment category
CC_PAYMENT_CATEGORY_SLUG = "credit-card-payment"

# Patterns for detecting income transactions based on description
INCOME_PATTERNS = [
    # Payroll patterns
    r"(?i)\b(payroll|direct\s*dep(osit)?|salary|wages|net\s*pay)\b",
    r"(?i)\b(adp|gusto|paychex|workday|paylocity|paycom)\b",
    # Interest patterns
    r"(?i)\b(interest\s*(payment|earned|credit|paid|income))\b",
    r"(?i)\b(apy\s*interest|savings\s*interest)\b",
    # Dividend patterns
    r"(?i)\b(dividend|div\s*payment|quarterly\s*div)\b",
    r"(?i)\b(capital\s*gain\s*dist|fund\s*distribution)\b",
    # Tax refund patterns
    r"(?i)\b(irs\s*treas|tax\s*refund|tax\s*ref)\b",
    r"(?i)\b(state\s*tax|federal\s*tax)\s*refund\b",
]

# Patterns for transfers (not income, not expense)
TRANSFER_PATTERNS = [
    r"(?i)\b(transfer|xfer|internal\s*transfer)\b",
    r"(?i)\b(zelle|venmo|cash\s*app|paypal|apple\s*cash)\b",
    r"(?i)\b(wire\s*transfer|ach\s*transfer)\b",
]

# Patterns for credit card payments (not an expense)
CC_PAYMENT_PATTERNS = [
    r"(?i)\b(payment\s*thank\s*you|autopay|auto\s*pay)\b",
    r"(?i)\b(credit\s*card\s*payment|card\s*payment)\b",
    r"(?i)\b(online\s*payment|payment\s*received)\b",
]


class TellerSyncService:
    """Refactored service for syncing Teller data to unified transaction model."""

    def __init__(self):
        self.account_repository = FinancialAccountRepository()
        self.transaction_repository = TransactionRepository()
        self.job_repository = SyncJobRepository()

    def _detect_transaction_nature(
        self,
        description: str,
        amount_raw: Decimal,
        account_type: str,
        teller_type: str,
    ) -> Tuple[str, Optional[str]]:
        """
        Detect the nature of a transaction based on multiple signals.

        Returns:
            Tuple of (transaction_type, hint) where:
            - transaction_type: "debit" or "credit"
            - hint: Optional category hint like "income", "transfer", "cc_payment"
        """
        hint = None

        # Check for income patterns first
        for pattern in INCOME_PATTERNS:
            if re.search(pattern, description):
                # If it matches income pattern AND is a deposit (positive for bank)
                if amount_raw > 0 and account_type != "credit_card":
                    hint = "income"
                    return ("credit", hint)
                break

        # Check for transfer patterns
        for pattern in TRANSFER_PATTERNS:
            if re.search(pattern, description):
                hint = "transfer"
                break

        # Check for credit card payment patterns (on credit card accounts)
        if account_type == "credit_card":
            for pattern in CC_PAYMENT_PATTERNS:
                if re.search(pattern, description):
                    hint = "cc_payment"
                    # Payments to credit card are credits (reduce balance)
                    return ("credit", hint)

        # ACH deposits to bank accounts are often income
        if teller_type == "ach" and amount_raw > 0 and account_type != "credit_card":
            # ACH credits are commonly payroll or transfers
            if not hint:
                hint = "potential_income"

        # Default logic based on account type and amount sign
        # For credit cards: positive = purchase (expense), negative = payment/refund
        # For bank accounts: positive = deposit (income), negative = withdrawal (expense)
        if account_type == "credit_card":
            transaction_type = "debit" if amount_raw > 0 else "credit"
        else:
            transaction_type = "credit" if amount_raw > 0 else "debit"

        return (transaction_type, hint)

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

    def _sync_account_balance(
        self, connection: SyncConnection, client: TellerClient
    ) -> Optional[Decimal]:
        """
        Sync account balance from Teller API.

        Args:
            connection: SyncConnection to sync balance for
            client: TellerClient instance

        Returns:
            The synced balance or None if failed
        """
        try:
            balance_data = client.get_account_balance(connection.external_account_id)

            # Use ledger balance (posted transactions) as the primary balance
            ledger_balance = balance_data.get("ledger")
            if ledger_balance is not None:
                balance = Decimal(str(ledger_balance))

                # Update the financial account balance AND record history
                account = connection.account
                self.account_repository.update_balance(account, balance)

                logger.info(
                    f"Synced balance for account {account.id} ({account.name}): {balance}"
                )
                return balance

            return None

        except Exception as e:
            logger.error(
                f"Error syncing balance for connection {connection.id}: {str(e)}"
            )
            return None

    def _get_cc_payment_category(self, user) -> Optional[TransactionCategory]:
        """
        Get the Credit Card Payment category for a user.

        Args:
            user: User to get category for

        Returns:
            TransactionCategory or None if not found
        """
        try:
            # Get user-specific credit card payment category
            category = TransactionCategory.objects.filter(
                user=user,
                slug=CC_PAYMENT_CATEGORY_SLUG,
            ).first()
            return category
        except Exception as e:
            logger.error(f"Error getting CC payment category: {str(e)}")
            return None

    def _categorize_by_keywords(self, transaction) -> Optional[TransactionCategory]:
        """
        Attempt to categorize a transaction using keyword matching.

        Args:
            transaction: Transaction to categorize

        Returns:
            TransactionCategory if matched, None otherwise
        """
        try:
            description_lower = transaction.description.lower()

            # Query all keywords for this user's categories
            # Order by match_count descending to prioritize effective keywords
            keywords = (
                CategoryKeyword.objects.filter(category__user=transaction.user)
                .select_related("category")
                .order_by("-match_count")
            )

            # Find first matching keyword
            for keyword_obj in keywords:
                if keyword_obj.keyword in description_lower:
                    logger.debug(
                        f"Keyword match for transaction {transaction.id}: "
                        f"'{keyword_obj.keyword}' → {keyword_obj.category.name}"
                    )
                    # Increment match count
                    keyword_obj.match_count += 1
                    keyword_obj.save(update_fields=["match_count"])
                    return keyword_obj.category

            return None
        except Exception as e:
            logger.error(f"Error in keyword categorization: {str(e)}")
            return None

    def sync_connection(
        self, connection: SyncConnection, force_full_sync: bool = False
    ) -> dict:
        """
        Sync transactions from Teller for a specific connection.

        On first sync (when initial_backfill_complete is False), this will
        automatically trigger a full historical sync.

        Args:
            connection: SyncConnection to sync
            force_full_sync: If True, perform full historical sync regardless

        Returns:
            dict with sync results
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

    def sync_historical_transactions(self, connection: SyncConnection) -> dict:
        """
        Sync all available historical transactions from Teller using pagination.

        Args:
            connection: SyncConnection to sync

        Returns:
            dict with sync results
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

            # Track oldest transaction date and categorization stats
            oldest_date = None
            total_synced = 0
            total_skipped = 0
            transactions_categorized = 0

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
                        # Extract Teller-specific fields for better categorization
                        teller_type = txn.get(
                            "type", ""
                        )  # ach, card, wire, check, etc.
                        teller_details = txn.get("details", {})
                        teller_category = (
                            teller_details.get("category", "") if teller_details else ""
                        )

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

                        # Determine transaction type using intelligent detection
                        # This considers description patterns, Teller type, and account type
                        transaction_type, nature_hint = self._detect_transaction_nature(
                            description=txn_description,
                            amount_raw=txn_amount_raw,
                            account_type=account.account_type,
                            teller_type=teller_type,
                        )

                        # Store hint in raw_data for use by categorization
                        txn["_nature_hint"] = nature_hint
                        txn["_teller_category"] = teller_category

                        # Create transaction
                        transaction = self.transaction_repository.create_transaction(
                            user=user,
                            account=account,
                            date=txn_date,
                            amount=txn_amount,
                            description=txn_description,
                            transaction_type=transaction_type,
                            status="posted",
                            sync_source="teller",
                            external_id=txn_id,
                            raw_data=txn,
                        )

                        # Auto-categorize during sync (rules + keywords)
                        categorized = self._auto_categorize_transaction(
                            transaction, nature_hint
                        )
                        if categorized:
                            transactions_categorized += 1

                        batch_synced += 1
                        total_synced += 1

                        # Update progress every 10 transactions for real-time feedback
                        if total_synced % 10 == 0:
                            job.transactions_synced = total_synced
                            job.transactions_skipped = total_skipped + batch_skipped
                            job.save(
                                update_fields=[
                                    "transactions_synced",
                                    "transactions_skipped",
                                ]
                            )

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
            results["transactions_categorized"] = transactions_categorized

            # Sync account balance from Teller
            synced_balance = self._sync_account_balance(connection, client)
            if synced_balance is not None:
                results["balance_synced"] = float(synced_balance)

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
                f"{transactions_categorized} categorized during sync."
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
    ) -> dict:
        """
        Sync recent transactions (last N days) for incremental updates.

        Args:
            connection: SyncConnection to sync
            days: Number of days to fetch (default 30)

        Returns:
            dict with sync results
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
            categorized_count = 0

            for txn in transactions:
                try:
                    txn_date = datetime.strptime(txn["date"], "%Y-%m-%d").date()
                    txn_amount_raw = Decimal(str(txn["amount"]))
                    txn_amount = abs(txn_amount_raw)
                    txn_description = txn.get("description", "")
                    txn_id = txn.get("id", "")
                    # Extract Teller-specific fields for better categorization
                    teller_type = txn.get("type", "")  # ach, card, wire, check, etc.
                    teller_details = txn.get("details", {})
                    teller_category = (
                        teller_details.get("category", "") if teller_details else ""
                    )

                    # Check if already exists
                    existing = self.transaction_repository.get_by_external_id(
                        user, txn_id, "teller"
                    )
                    if existing:
                        skipped_count += 1
                        continue

                    # Determine transaction type using intelligent detection
                    # This considers description patterns, Teller type, and account type
                    transaction_type, nature_hint = self._detect_transaction_nature(
                        description=txn_description,
                        amount_raw=txn_amount_raw,
                        account_type=account.account_type,
                        teller_type=teller_type,
                    )

                    # Store hint in raw_data for use by categorization
                    txn["_nature_hint"] = nature_hint
                    txn["_teller_category"] = teller_category

                    # Create transaction
                    transaction = self.transaction_repository.create_transaction(
                        user=user,
                        account=account,
                        date=txn_date,
                        amount=txn_amount,
                        description=txn_description,
                        transaction_type=transaction_type,
                        status="posted",
                        sync_source="teller",
                        external_id=txn_id,
                        raw_data=txn,
                    )

                    # Auto-categorize during sync (rules + keywords)
                    categorized = self._auto_categorize_transaction(
                        transaction, nature_hint
                    )
                    if categorized:
                        categorized_count += 1

                    synced_count += 1

                    # Update progress every 10 transactions for real-time feedback
                    if synced_count % 10 == 0:
                        job.transactions_synced = synced_count
                        job.transactions_skipped = skipped_count
                        job.save(
                            update_fields=[
                                "transactions_synced",
                                "transactions_skipped",
                            ]
                        )

                except Exception as e:
                    logger.error(f"Error syncing transaction {txn.get('id')}: {str(e)}")
                    results["errors"].append(str(e))
                    continue

            # Final progress update
            job.transactions_synced = synced_count
            job.transactions_skipped = skipped_count
            job.save(update_fields=["transactions_synced", "transactions_skipped"])

            results["transactions_synced"] = synced_count
            results["transactions_skipped"] = skipped_count
            results["transactions_categorized"] = categorized_count

            # Sync account balance from Teller
            synced_balance = self._sync_account_balance(connection, client)
            if synced_balance is not None:
                results["balance_synced"] = float(synced_balance)

            # Mark connection as synced
            connection.mark_synced()

            # Mark job as completed
            job.mark_completed(synced_count, skipped_count)

            results["success"] = True
            results["message"] = (
                f"Successfully synced {synced_count} new transactions, "
                f"skipped {skipped_count} duplicates. "
                f"{categorized_count} categorized during sync."
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

    def _transaction_type_from_category(self, category: TransactionCategory) -> str:
        """
        Determine transaction type (debit/credit) from category type.

        Args:
            category: TransactionCategory instance

        Returns:
            "debit" or "credit"
        """
        # Income categories are credits (money coming in)
        if category.type == "income":
            return "credit"
        # Expense categories are debits (money going out)
        elif category.type == "expense":
            return "debit"
        # Transfers can be either, keep existing type
        else:  # transfer
            return "debit"  # Default to debit for transfers

    def _auto_categorize_transaction(
        self, transaction, nature_hint: Optional[str] = None
    ) -> bool:
        """
        Attempt to categorize transaction during sync using keyword matching.

        Args:
            transaction: Transaction to categorize
            nature_hint: Optional hint about transaction nature (deprecated, not used)

        Returns:
            True if categorized, False if uncategorized
        """
        try:
            # Single stage: keyword matching
            category = self._categorize_by_keywords(transaction)
            if category:
                transaction.category = category
                # Category type determines transaction type
                transaction.transaction_type = self._transaction_type_from_category(
                    category
                )
                transaction.categorization_status = "categorized"
                transaction.save()
                logger.debug(
                    f"Categorized transaction {transaction.id}: {category.name} ({category.type})"
                )
                return True

            # No match found - leave as uncategorized
            transaction.categorization_status = "uncategorized"
            transaction.save()
            return False

        except Exception as e:
            logger.error(f"Error in auto-categorization: {str(e)}")
            return False
