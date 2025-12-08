"""Plaid sync service for syncing bank data to unified transaction model."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from apps.categorization.services.rule_based_service import (
    RuleBasedCategorizationService,
)
from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.sync.models import SyncConnection
from apps.sync.repositories.sync_job_repository import SyncJobRepository
from apps.transaction.models import TransactionCategory
from apps.transaction.repositories.merchant_repository import MerchantRepository
from apps.transaction.repositories.transaction_repository import TransactionRepository
from categories.categories import BaseCategory
from django.conf import settings
from integrations.plaid.client import PlaidClient
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
        self.merchant_repository = MerchantRepository()
        self.job_repository = SyncJobRepository()
        self.rule_categorization = RuleBasedCategorizationService()

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
        plaid_category: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Detect the nature of a transaction based on multiple signals.

        Note: Plaid amounts are OPPOSITE of Teller:
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

    def _sync_account_balance(
        self, connection: SyncConnection, client: PlaidClient
    ) -> Optional[Decimal]:
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
        """Get the Credit Card Payment category for a user."""
        try:
            category = TransactionCategory.objects.filter(
                user=user,
                slug=CC_PAYMENT_CATEGORY_SLUG,
            ).first()

            if not category:
                category = TransactionCategory.objects.filter(
                    user__isnull=True,
                    slug=CC_PAYMENT_CATEGORY_SLUG,
                ).first()

            return category
        except Exception as e:
            logger.error(f"Error getting CC payment category: {str(e)}")
            return None

    def _ensure_user_categories_exist(self, user) -> None:
        """Ensure categories exist for a user, creating them if necessary."""
        existing_count = TransactionCategory.objects.filter(user=user).count()
        if existing_count > 0:
            return

        category_classes = BaseCategory.get_registered_categories()
        created_count = 0

        for cat_instance in category_classes:
            try:
                from django.utils.text import slugify

                slug = slugify(cat_instance.name)

                TransactionCategory.objects.get_or_create(
                    user=user,
                    slug=slug,
                    defaults={
                        "name": cat_instance.name,
                        "icon": cat_instance.icon,
                        "color": cat_instance.color,
                        "is_income": cat_instance.is_income,
                        "is_expense": cat_instance.is_expense,
                    },
                )
                created_count += 1
            except Exception as e:
                logger.warning(f"Could not create category {cat_instance.name}: {e}")
                continue

        if created_count > 0:
            logger.info(f"Created {created_count} categories for user {user.username}")

    def _get_keyword_category_map(self, user) -> Dict[str, TransactionCategory]:
        """Build a keyword to category mapping for a user."""
        self._ensure_user_categories_exist(user)

        keyword_map = {}
        category_class_map = BaseCategory.get_registry()

        user_categories = list(TransactionCategory.objects.filter(user=user))
        global_categories = list(TransactionCategory.objects.filter(user__isnull=True))

        all_categories = user_categories + global_categories

        for category in all_categories:
            category_class = category_class_map.get(category.name)
            if not category_class:
                continue

            try:
                instance = category_class()
                for keyword in instance.generate_keywords():
                    keyword_lower = keyword.strip().lower()
                    if keyword_lower not in keyword_map or category.user is not None:
                        keyword_map[keyword_lower] = category
            except Exception:
                continue

        return keyword_map

    def _categorize_by_keywords(
        self, transaction, description: str, user
    ) -> Optional[TransactionCategory]:
        """Attempt to categorize a transaction using keyword matching."""
        try:
            keyword_map = self._get_keyword_category_map(user)
            description_lower = description.lower()

            for keyword, category in keyword_map.items():
                if keyword in description_lower:
                    logger.debug(
                        f"Keyword match for transaction {transaction.id}: "
                        f"'{keyword}' → {category.name}"
                    )
                    return category

            return None
        except Exception as e:
            logger.error(f"Error in keyword categorization: {str(e)}")
            return None

    def sync_connection(
        self, connection: SyncConnection, force_full_sync: bool = False
    ) -> Dict:
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
            logger.info(
                f"Triggering full historical sync for Plaid connection {connection.id}"
            )
            return self.sync_historical_transactions(connection)
        else:
            logger.info(
                f"Triggering incremental sync for Plaid connection {connection.id}"
            )
            return self.sync_recent_transactions(connection)

    def sync_historical_transactions(self, connection: SyncConnection) -> Dict:
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

                logger.info(
                    f"Processing batch {results['batches_processed']} "
                    f"with {len(batch)} transactions"
                )

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
                        plaid_category = (
                            plaid_details.get("category", {}).get("primary", "")
                            if plaid_details
                            else ""
                        )

                        # Track oldest date
                        if oldest_date is None or txn_date < oldest_date:
                            oldest_date = txn_date

                        # Check if already exists
                        existing = self.transaction_repository.get_by_external_id(
                            user, txn_id, "plaid"
                        )
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

                        # Get or create merchant
                        merchant = None
                        merchant_data = txn.get("merchant")
                        if merchant_data and isinstance(merchant_data, dict):
                            merchant_name = merchant_data.get("name")
                            if merchant_name:
                                merchant = (
                                    self.merchant_repository.get_or_create_merchant(
                                        name=merchant_name
                                    )
                                )

                        # Create transaction (serialize raw_data to handle date objects)
                        transaction = self.transaction_repository.create_transaction(
                            user=user,
                            account=account,
                            date=txn_date,
                            amount=txn_amount,
                            description=txn_description,
                            transaction_type=transaction_type,
                            merchant=merchant,
                            status=txn.get("status", "posted"),
                            sync_source="plaid",
                            external_id=txn_id,
                            raw_data=self._serialize_plaid_data(txn),
                        )

                        categorized = self._auto_categorize_transaction(
                            transaction, nature_hint
                        )
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

            connection.mark_synced(backfill_complete=True, oldest_date=oldest_date)
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
    ) -> Dict:
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

            transaction_limit = min(
                getattr(settings, "PLAID_TRANSACTION_LIMIT", 500), 100
            )
            transactions = client.get_transactions(
                connection.external_account_id, count=transaction_limit
            )

            logger.info(
                f"Fetched {len(transactions)} recent transactions for "
                f"Plaid connection {connection.id}"
            )

            synced_count = 0
            skipped_count = 0
            categorized_count = 0

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

                    plaid_details = txn.get("details", {})
                    plaid_category = (
                        plaid_details.get("category", {}).get("primary", "")
                        if plaid_details
                        else ""
                    )

                    existing = self.transaction_repository.get_by_external_id(
                        user, txn_id, "plaid"
                    )
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

                    merchant = None
                    merchant_data = txn.get("merchant")
                    if merchant_data and isinstance(merchant_data, dict):
                        merchant_name = merchant_data.get("name")
                        if merchant_name:
                            merchant = self.merchant_repository.get_or_create_merchant(
                                name=merchant_name
                            )

                    # Serialize raw_data to handle date objects
                    transaction = self.transaction_repository.create_transaction(
                        user=user,
                        account=account,
                        date=txn_date,
                        amount=txn_amount,
                        description=txn_description,
                        transaction_type=transaction_type,
                        merchant=merchant,
                        status=txn.get("status", "posted"),
                        sync_source="plaid",
                        external_id=txn_id,
                        raw_data=self._serialize_plaid_data(txn),
                    )

                    categorized = self._auto_categorize_transaction(
                        transaction, nature_hint
                    )
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

            connection.mark_synced()
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

    def _auto_categorize_transaction(
        self, transaction, nature_hint: Optional[str] = None
    ) -> bool:
        """
        Attempt to categorize transaction during sync.

        Categorization order:
        1. CC payment hint
        2. User-defined rules
        3. Keyword-based matching

        Returns:
            True if categorized, False otherwise
        """
        try:
            if nature_hint == "cc_payment":
                cc_payment_category = self._get_cc_payment_category(transaction.user)
                if cc_payment_category:
                    transaction.category = cc_payment_category
                    transaction.categorization_status = "categorized"
                    transaction.save()
                    logger.debug(
                        f"Auto-categorized transaction {transaction.id} as Credit Card Payment"
                    )
                    return True

            rule_result = self.rule_categorization.categorize_transaction(transaction)
            if rule_result:
                category, rule = rule_result
                self.rule_categorization.apply_categorization(
                    transaction, category, rule
                )
                transaction.categorization_status = "categorized"
                transaction.save()
                return True

            keyword_category = self._categorize_by_keywords(
                transaction, transaction.description, transaction.user
            )
            if keyword_category:
                transaction.category = keyword_category
                transaction.categorization_status = "categorized"
                transaction.save()
                logger.debug(
                    f"Keyword-categorized transaction {transaction.id}: {keyword_category.name}"
                )
                return True

            transaction.categorization_status = "uncategorized"
            transaction.save()
            return False

        except Exception as e:
            logger.error(f"Error in auto-categorization: {str(e)}")
            return False
