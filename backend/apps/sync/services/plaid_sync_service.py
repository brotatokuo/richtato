"""Plaid sync service for syncing bank data to unified transaction model."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.conf import settings
from loguru import logger

from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.sync.models import SyncConnection
from apps.sync.repositories.sync_job_repository import SyncJobRepository
from apps.transaction.models import CategoryKeyword, TransactionCategory
from apps.transaction.repositories.transaction_repository import TransactionRepository
from integrations.plaid.client import PlaidClient

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

# Plaid category mappings to our system
PLAID_CATEGORY_MAP = {
    "INCOME": "income",
    "TRANSFER_IN": "transfer",
    "TRANSFER_OUT": "transfer",
    "LOAN_PAYMENTS": "cc_payment",
    "BANK_FEES": "fees",
    "ENTERTAINMENT": "entertainment",
    "FOOD_AND_DRINK": "food",
    "GENERAL_MERCHANDISE": "shopping",
    "GENERAL_SERVICES": "services",
    "GOVERNMENT_AND_NON_PROFIT": "taxes",
    "HOME_IMPROVEMENT": "home",
    "MEDICAL": "healthcare",
    "PERSONAL_CARE": "personal",
    "RENT_AND_UTILITIES": "bills",
    "TRANSPORTATION": "transportation",
    "TRAVEL": "travel",
}


class PlaidSyncService:
    """Service for syncing Plaid data to unified transaction model."""

    def __init__(self):
        self.account_repository = FinancialAccountRepository()
        self.transaction_repository = TransactionRepository()
        self.job_repository = SyncJobRepository()

    def _serialize_plaid_data(self, data) -> Any:
        """
        Serialize Plaid transaction data for JSON storage.
        Converts date objects to ISO format strings and Plaid SDK objects to dicts.
        """
        from datetime import date as date_type

        def serialize_value(val):
            # Handle Plaid SDK objects that have to_dict method
            if hasattr(val, "to_dict"):
                return serialize_value(val.to_dict())
            # Handle date objects
            elif isinstance(val, date_type):
                return val.isoformat()
            elif isinstance(val, dict):
                return {k: serialize_value(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [serialize_value(item) for item in val]
            return val

        return serialize_value(data)

    def _detect_transaction_nature(
        self,
        description: str,
        amount_raw: Decimal,
        account_type: str,
        plaid_category: str | None = None,
    ) -> tuple[str, str | None]:
        """
        Detect the nature of a transaction based on multiple signals.

        Note: Plaid amounts are:
        - Plaid: positive = money leaving account (expense), negative = money entering (income)
        - This method normalizes to our internal convention

        Returns:
            Tuple of (transaction_type, hint) where:
            - transaction_type: "debit" or "credit"
            - hint: Optional category hint like "income", "transfer", "cc_payment"
        """
        hint = None

        # Check Plaid's own category first
        if plaid_category:
            plaid_hint = PLAID_CATEGORY_MAP.get(plaid_category.upper())
            if plaid_hint:
                hint = plaid_hint
                # If Plaid says it's income, trust that
                if plaid_hint == "income":
                    return ("credit", hint)
                elif plaid_hint == "transfer":
                    # Determine direction based on amount
                    return ("credit" if amount_raw < 0 else "debit", hint)

        # Check for income patterns
        for pattern in INCOME_PATTERNS:
            if re.search(pattern, description):
                # In Plaid, negative amounts are money coming in
                if amount_raw < 0 and account_type != "credit_card":
                    hint = "income"
                    return ("credit", hint)
                break

        # Check for transfer patterns
        for pattern in TRANSFER_PATTERNS:
            if re.search(pattern, description):
                hint = "transfer"
                break

        # Check for credit card payment patterns
        if account_type == "credit_card":
            for pattern in CC_PAYMENT_PATTERNS:
                if re.search(pattern, description):
                    hint = "cc_payment"
                    return ("credit", hint)

        # Default logic based on Plaid amount convention:
        # Plaid: positive = outflow (expense/debit), negative = inflow (income/credit)
        # For credit cards: positive = purchase (expense), negative = payment/refund
        # For bank accounts: positive = withdrawal (expense), negative = deposit (income)
        if amount_raw > 0:
            transaction_type = "debit"  # Money leaving
        else:
            transaction_type = "credit"  # Money entering

        return (transaction_type, hint)

    def _get_plaid_client(self, connection: SyncConnection) -> PlaidClient:
        """Create a PlaidClient instance for the connection."""
        client_id = getattr(settings, "PLAID_CLIENT_ID", None)
        secret = getattr(settings, "PLAID_SECRET", None)
        environment = getattr(settings, "PLAID_ENV", "sandbox")

        if not client_id or not secret:
            raise ValueError("Plaid credentials not configured in settings")

        return PlaidClient(
            client_id=client_id,
            secret=secret,
            environment=environment,
            access_token=connection.access_token,
        )

    def _sync_account_balance(self, connection: SyncConnection, client: PlaidClient) -> Decimal | None:
        """
        Sync account balance from Plaid API.

        Args:
            connection: SyncConnection to sync balance for
            client: PlaidClient instance

        Returns:
            The synced balance or None if failed
        """
        try:
            balance_data = client.get_account_balance(connection.external_account_id)

            ledger_balance = balance_data.get("ledger")
            if ledger_balance is not None:
                balance = Decimal(str(ledger_balance))

                account = connection.account
                # Plaid reports liabilities as positive; store negative
                if account.is_liability and balance > 0:
                    balance = -balance
                self.account_repository.update_balance(account, balance, source="plaid_sync")

                logger.info(f"Synced balance for account {account.id} ({account.name}): {balance}")
                return balance

            return None

        except Exception as e:
            logger.error(f"Error syncing balance for connection {connection.id}: {str(e)}")
            return None

    def _categorize_by_keywords(self, transaction) -> TransactionCategory | None:
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

    def sync_connection(self, connection: SyncConnection, force_full_sync: bool = False) -> dict:
        """
        Sync transactions from Plaid for a specific connection.

        Args:
            connection: SyncConnection to sync
            force_full_sync: If True, perform full sync regardless

        Returns:
            Dict with sync results
        """
        is_full_sync = not connection.initial_backfill_complete or force_full_sync

        if is_full_sync:
            logger.info(f"Triggering full historical sync for Plaid connection {connection.id}")
            return self.sync_historical_transactions(connection)
        else:
            logger.info(f"Triggering incremental sync for Plaid connection {connection.id}")
            return self.sync_recent_transactions(connection)

    def sync_historical_transactions(self, connection: SyncConnection) -> dict:
        """
        Sync all available transactions from Plaid using cursor-based sync.

        Args:
            connection: SyncConnection to sync

        Returns:
            Dict with sync results
        """
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
            client = self._get_plaid_client(connection)
            user = connection.user
            account = connection.account

            oldest_date = None
            newest_date = None
            total_synced = 0
            total_skipped = 0
            transactions_categorized = 0

            logger.info(
                f"Starting historical sync for Plaid connection {connection.id} "
                f"(account: {connection.external_account_id})"
            )

            batch_size = getattr(settings, "PLAID_TRANSACTION_LIMIT", 500)
            for batch in client.get_transactions_paginated(
                account_id=connection.external_account_id,
                batch_size=batch_size,
            ):
                results["batches_processed"] += 1
                batch_synced = 0
                batch_skipped = 0

                logger.info(f"Processing batch {results['batches_processed']} with {len(batch)} transactions")

                for txn in batch:
                    try:
                        # Handle both date objects (from Plaid SDK) and strings
                        raw_date = txn["date"]
                        if isinstance(raw_date, str):
                            txn_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                        else:
                            txn_date = raw_date  # Already a date object
                        txn_amount_raw = Decimal(str(txn["amount"]))
                        # Plaid amounts are positive for expenses, so we take absolute value
                        txn_amount = abs(txn_amount_raw)
                        txn_description = txn.get("description", "")
                        txn_id = txn.get("id", "")

                        # Extract Plaid-specific category
                        plaid_details = txn.get("details", {})
                        plaid_category = plaid_details.get("category", {}).get("primary", "") if plaid_details else ""

                        # Track oldest and newest dates
                        if oldest_date is None or txn_date < oldest_date:
                            oldest_date = txn_date
                        if newest_date is None or txn_date > newest_date:
                            newest_date = txn_date

                        # Check if already exists
                        existing = self.transaction_repository.get_by_external_id(user, txn_id, "plaid")
                        if existing:
                            batch_skipped += 1
                            continue

                        # Determine transaction type
                        transaction_type, nature_hint = self._detect_transaction_nature(
                            description=txn_description,
                            amount_raw=txn_amount_raw,
                            account_type=account.account_type,
                            plaid_category=plaid_category,
                        )

                        # Store hints in raw_data
                        txn["_nature_hint"] = nature_hint
                        txn["_plaid_category"] = plaid_category

                        # Create transaction (serialize raw_data to handle date objects)
                        transaction = self.transaction_repository.create_transaction(
                            user=user,
                            account=account,
                            date=txn_date,
                            amount=txn_amount,
                            description=txn_description,
                            transaction_type=transaction_type,
                            status=txn.get("status", "posted"),
                            sync_source="plaid",
                            external_id=txn_id,
                            raw_data=self._serialize_plaid_data(txn),
                        )

                        categorized = self._auto_categorize_transaction(transaction, nature_hint)
                        if categorized:
                            transactions_categorized += 1

                        batch_synced += 1
                        total_synced += 1

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
                        logger.error(f"Error syncing transaction {txn.get('id')}: {str(e)}")
                        results["errors"].append(str(e))
                        continue

                total_skipped += batch_skipped

                logger.info(f"Batch {results['batches_processed']}: synced {batch_synced}, skipped {batch_skipped}")

                job.transactions_synced = total_synced
                job.transactions_skipped = total_skipped
                job.batches_processed = results["batches_processed"]
                job.save()

            results["transactions_synced"] = total_synced
            results["transactions_skipped"] = total_skipped
            results["transactions_categorized"] = transactions_categorized

            synced_balance = self._sync_account_balance(connection, client)
            if synced_balance is not None:
                results["balance_synced"] = float(synced_balance)

            connection.mark_synced(backfill_complete=True, oldest_date=oldest_date, newest_date=newest_date)
            job.mark_completed(total_synced, total_skipped)

            results["success"] = True
            results["message"] = (
                f"Successfully synced {total_synced} transactions, "
                f"skipped {total_skipped} duplicates across "
                f"{results['batches_processed']} batches. "
                f"Date range: {oldest_date if oldest_date else 'N/A'} to "
                f"{newest_date if newest_date else 'N/A'}. "
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

    def sync_recent_transactions(self, connection: SyncConnection, days: int = 30) -> dict:
        """
        Sync recent transactions for incremental updates.

        Args:
            connection: SyncConnection to sync
            days: Number of days to fetch (default 30)

        Returns:
            Dict with sync results
        """
        job = self.job_repository.create_job(connection, is_full_sync=False)

        results = {
            "success": False,
            "transactions_synced": 0,
            "transactions_skipped": 0,
            "errors": [],
            "message": "",
        }

        try:
            client = self._get_plaid_client(connection)
            user = connection.user
            account = connection.account

            # Get the last synced transaction date for filtering
            last_synced_date = connection.newest_transaction_date
            if last_synced_date:
                logger.info(
                    f"Incremental sync: will skip transactions on or before "
                    f"{last_synced_date} for Plaid connection {connection.id}"
                )

            transaction_limit = min(getattr(settings, "PLAID_TRANSACTION_LIMIT", 500), 100)
            transactions = client.get_transactions(connection.external_account_id, count=transaction_limit)

            logger.info(f"Fetched {len(transactions)} transactions for Plaid connection {connection.id}")

            synced_count = 0
            skipped_count = 0
            categorized_count = 0
            newest_date = connection.newest_transaction_date  # Start with existing

            for txn in transactions:
                try:
                    # Handle both date objects (from Plaid SDK) and strings
                    raw_date = txn["date"]
                    if isinstance(raw_date, str):
                        txn_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                    else:
                        txn_date = raw_date  # Already a date object
                    txn_amount_raw = Decimal(str(txn["amount"]))
                    txn_amount = abs(txn_amount_raw)
                    txn_description = txn.get("description", "")
                    txn_id = txn.get("id", "")

                    # Track newest date for future incremental syncs
                    if newest_date is None or txn_date > newest_date:
                        newest_date = txn_date

                    # Skip transactions on or before the last synced date
                    # (Plaid doesn't support date filtering at API level, so we filter here)
                    if last_synced_date and txn_date <= last_synced_date:
                        skipped_count += 1
                        continue

                    plaid_details = txn.get("details", {})
                    plaid_category = plaid_details.get("category", {}).get("primary", "") if plaid_details else ""

                    existing = self.transaction_repository.get_by_external_id(user, txn_id, "plaid")
                    if existing:
                        skipped_count += 1
                        continue

                    transaction_type, nature_hint = self._detect_transaction_nature(
                        description=txn_description,
                        amount_raw=txn_amount_raw,
                        account_type=account.account_type,
                        plaid_category=plaid_category,
                    )

                    txn["_nature_hint"] = nature_hint
                    txn["_plaid_category"] = plaid_category

                    # Serialize raw_data to handle date objects
                    transaction = self.transaction_repository.create_transaction(
                        user=user,
                        account=account,
                        date=txn_date,
                        amount=txn_amount,
                        description=txn_description,
                        transaction_type=transaction_type,
                        status=txn.get("status", "posted"),
                        sync_source="plaid",
                        external_id=txn_id,
                        raw_data=self._serialize_plaid_data(txn),
                    )

                    categorized = self._auto_categorize_transaction(transaction, nature_hint)
                    if categorized:
                        categorized_count += 1

                    synced_count += 1

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

            job.transactions_synced = synced_count
            job.transactions_skipped = skipped_count
            job.save(update_fields=["transactions_synced", "transactions_skipped"])

            results["transactions_synced"] = synced_count
            results["transactions_skipped"] = skipped_count
            results["transactions_categorized"] = categorized_count

            synced_balance = self._sync_account_balance(connection, client)
            if synced_balance is not None:
                results["balance_synced"] = float(synced_balance)

            # Mark connection as synced with updated newest_date
            connection.mark_synced(newest_date=newest_date)
            job.mark_completed(synced_count, skipped_count)

            results["success"] = True
            results["message"] = (
                f"Successfully synced {synced_count} new transactions, "
                f"skipped {skipped_count} duplicates. "
                f"Newest transaction: {newest_date if newest_date else 'N/A'}. "
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

    def _auto_categorize_transaction(self, transaction, nature_hint: str | None = None) -> bool:
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
                transaction.transaction_type = self._transaction_type_from_category(category)
                transaction.categorization_status = "categorized"
                transaction.save()
                logger.debug(f"Categorized transaction {transaction.id}: {category.name} ({category.type})")
                return True

            # No match found - leave as uncategorized
            transaction.categorization_status = "uncategorized"
            transaction.save()
            return False

        except Exception as e:
            logger.error(f"Error in auto-categorization: {str(e)}")
            return False
