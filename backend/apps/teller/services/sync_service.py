"""Sync service for fetching and mapping Teller transactions."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from apps.account.repositories.account_repository import AccountRepository
from apps.card.models import CardAccount
from apps.card.repositories.card_account_repository import CardAccountRepository
from apps.expense.repositories.expense_repository import ExpenseRepository
from apps.richtato_user.models import User
from apps.teller.models import TellerConnection
from django.conf import settings
from integrations.teller.client import TellerClient
from loguru import logger


class TellerSyncService:
    """Service for syncing Teller data to local database."""

    def __init__(self):
        self.account_repository = AccountRepository()
        self.expense_repository = ExpenseRepository()
        self.card_repository = CardAccountRepository()

    def _get_teller_client(self, connection: TellerConnection) -> TellerClient:
        """
        Create a TellerClient instance for the connection.

        Args:
            connection: TellerConnection instance

        Returns:
            Initialized TellerClient
        """
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
        self,
        connection: TellerConnection,
        days: int = 30,
        force_full_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Sync transactions from Teller for a specific connection.

        On first sync (when initial_backfill_complete is False), this will
        automatically trigger a full historical sync. Subsequent syncs will
        only fetch recent transactions (last N days).

        Args:
            connection: TellerConnection to sync
            days: Number of days to fetch transactions for (default 30)
            force_full_sync: If True, perform full historical sync regardless of backfill status

        Returns:
            Dict with sync results including counts and errors
        """
        # Check if this is the first sync or a forced full sync
        if not connection.initial_backfill_complete or force_full_sync:
            logger.info(
                f"Triggering historical transaction sync for connection {connection.id} "
                f"(first_sync={not connection.initial_backfill_complete}, "
                f"force_full_sync={force_full_sync})"
            )
            return self.sync_historical_transactions(connection)

        # Regular incremental sync for subsequent syncs
        user = connection.user
        results = {
            "success": False,
            "accounts_synced": 0,
            "transactions_synced": 0,
            "errors": [],
            "message": "",
        }

        try:
            # Initialize Teller client
            client = self._get_teller_client(connection)

            # Fetch accounts from Teller
            teller_accounts = client.get_accounts()
            logger.info(
                f"Fetched {len(teller_accounts)} accounts from Teller "
                f"for connection {connection.id}"
            )

            # Find the specific account for this connection
            teller_account = None
            for acc in teller_accounts:
                if acc.get("id") == connection.teller_account_id:
                    teller_account = acc
                    break

            if not teller_account:
                error_msg = (
                    f"Account {connection.teller_account_id} not found in Teller"
                )
                logger.error(error_msg)
                results["errors"].append(error_msg)
                connection.mark_error(error_msg)
                return results

            # Sync account balance
            account_synced = self._sync_account_balance(
                user, connection, teller_account
            )
            if account_synced:
                results["accounts_synced"] += 1

            # Fetch transactions
            transactions = client.get_transactions(
                connection.teller_account_id, count=100
            )

            # Filter transactions by date range
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            filtered_transactions = client.filter_transactions(
                transactions, start_date=start_date
            )

            logger.info(
                f"Fetched {len(filtered_transactions)} transactions for account "
                f"{connection.teller_account_id}"
            )

            # Sync transactions
            synced_count = self._sync_transactions(
                user, connection, teller_account, filtered_transactions
            )
            results["transactions_synced"] = synced_count

            # Mark connection as successfully synced
            connection.mark_synced()

            results["success"] = True
            results["message"] = (
                f"Successfully synced {results['accounts_synced']} accounts and "
                f"{results['transactions_synced']} transactions"
            )

        except Exception as e:
            error_msg = f"Error syncing connection {connection.id}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["message"] = error_msg
            connection.mark_error(error_msg)

        return results

    def sync_historical_transactions(
        self, connection: TellerConnection
    ) -> Dict[str, Any]:
        """
        Sync all available historical transactions from Teller using pagination.

        This method fetches transactions in batches until all available history
        is retrieved. It's designed for initial backfill or full re-sync.

        Args:
            connection: TellerConnection to sync

        Returns:
            Dict with sync results including counts and errors
        """
        user = connection.user
        results = {
            "success": False,
            "accounts_synced": 0,
            "transactions_synced": 0,
            "batches_processed": 0,
            "errors": [],
            "message": "",
        }

        try:
            # Initialize Teller client
            client = self._get_teller_client(connection)

            # Fetch accounts from Teller
            teller_accounts = client.get_accounts()
            logger.info(
                f"Fetched {len(teller_accounts)} accounts from Teller "
                f"for connection {connection.id}"
            )

            # Find the specific account for this connection
            teller_account = None
            for acc in teller_accounts:
                if acc.get("id") == connection.teller_account_id:
                    teller_account = acc
                    break

            if not teller_account:
                error_msg = (
                    f"Account {connection.teller_account_id} not found in Teller"
                )
                logger.error(error_msg)
                results["errors"].append(error_msg)
                connection.mark_error(error_msg)
                return results

            # Sync account balance
            account_synced = self._sync_account_balance(
                user, connection, teller_account
            )
            if account_synced:
                results["accounts_synced"] += 1

            # Get or create CardAccount for these transactions
            card_account = self._get_or_create_card_account(user, connection)

            # Track the oldest transaction date we've synced
            oldest_date = None
            total_synced = 0

            # Fetch transactions in batches using pagination
            logger.info(
                f"Starting historical transaction sync for account "
                f"{connection.teller_account_id}"
            )

            for batch in client.get_transactions_paginated(
                account_id=connection.teller_account_id,
                batch_size=500,
            ):
                results["batches_processed"] += 1
                batch_synced = 0

                logger.info(
                    f"Processing batch {results['batches_processed']} "
                    f"with {len(batch)} transactions"
                )

                for txn in batch:
                    try:
                        txn_date = datetime.strptime(txn["date"], "%Y-%m-%d").date()
                        txn_amount_raw = Decimal(str(txn["amount"]))
                        txn_amount = abs(txn_amount_raw)
                        txn_description = txn.get("description", "")

                        # Track oldest transaction date
                        if oldest_date is None or txn_date < oldest_date:
                            oldest_date = txn_date

                        # Check for duplicates
                        if self._is_duplicate_transaction(
                            user, txn_date, txn_amount, txn_description
                        ):
                            continue

                        # Only sync debit transactions (expenses)
                        if txn_amount_raw < 0:  # Negative amount = debit/expense
                            self.expense_repository.create_expense(
                                user=user,
                                account=card_account,
                                category=None,  # Will need to be categorized later
                                description=txn_description,
                                amount=txn_amount,
                                date=txn_date,
                            )
                            batch_synced += 1
                            total_synced += 1

                    except Exception as e:
                        logger.error(
                            f"Error syncing transaction {txn.get('id')}: {str(e)}"
                        )
                        continue

                logger.info(
                    f"Batch {results['batches_processed']}: synced {batch_synced} "
                    f"new transactions"
                )

            results["transactions_synced"] = total_synced

            # Mark connection as successfully synced with backfill complete
            connection.mark_synced(backfill_complete=True, oldest_date=oldest_date)

            results["success"] = True
            results["message"] = (
                f"Successfully synced {results['accounts_synced']} accounts and "
                f"{results['transactions_synced']} transactions across "
                f"{results['batches_processed']} batches. "
                f"Oldest transaction: {oldest_date if oldest_date else 'N/A'}"
            )

            logger.info(results["message"])

        except Exception as e:
            error_msg = f"Error syncing historical transactions for connection {connection.id}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["message"] = error_msg
            connection.mark_error(error_msg)

        return results

    def _sync_account_balance(
        self, user: User, connection: TellerConnection, teller_account: Dict
    ) -> bool:
        """
        Sync account balance from Teller to local Account model.

        Args:
            user: User instance
            connection: TellerConnection instance
            teller_account: Teller account data

        Returns:
            True if synced successfully
        """
        try:
            # Try to find existing account by name
            account_name = f"{connection.institution_name} - {connection.account_name}"
            accounts = self.account_repository.get_user_accounts(user)
            existing_account = None

            for acc in accounts:
                if acc.name == account_name:
                    existing_account = acc
                    break

            # Map Teller account type to our account types
            account_type = self._map_account_type(teller_account.get("type", ""))

            if existing_account:
                # Update existing account
                balance = Decimal(str(teller_account.get("balance", 0)))
                self.account_repository.update_account(
                    existing_account,
                    latest_balance=balance,
                    latest_balance_date=datetime.now().date(),
                )
                logger.info(
                    f"Updated account {existing_account.id} balance to {balance}"
                )
            else:
                # Create new account
                balance = Decimal(str(teller_account.get("balance", 0)))
                new_account = self.account_repository.create_account(
                    user=user,
                    name=account_name,
                    type=account_type,
                    asset_entity_name=self._map_institution_name(
                        connection.institution_name
                    ),
                    latest_balance=balance,
                    latest_balance_date=datetime.now().date(),
                )
                logger.info(
                    f"Created new account {new_account.id} with balance {balance}"
                )

            return True

        except Exception as e:
            logger.error(f"Error syncing account balance: {str(e)}")
            return False

    def _is_duplicate_transaction(
        self, user: User, txn_date, txn_amount: Decimal, txn_description: str
    ) -> bool:
        """
        Check if a transaction already exists in the database.

        Args:
            user: User instance
            txn_date: Transaction date
            txn_amount: Transaction amount (absolute value)
            txn_description: Transaction description

        Returns:
            True if transaction is a duplicate, False otherwise
        """
        existing_expenses = self.expense_repository.get_user_expenses(user)
        for exp in existing_expenses:
            if (
                exp.date == txn_date
                and abs(exp.amount - txn_amount) < Decimal("0.01")
                and exp.description == txn_description
            ):
                return True
        return False

    def _sync_transactions(
        self,
        user: User,
        connection: TellerConnection,
        teller_account: Dict,
        transactions: List[Dict],
    ) -> int:
        """
        Sync transactions from Teller to local Expense model.

        Args:
            user: User instance
            connection: TellerConnection instance
            teller_account: Teller account data
            transactions: List of Teller transactions

        Returns:
            Number of transactions synced
        """
        synced_count = 0

        # Get or create CardAccount for these transactions
        card_account = self._get_or_create_card_account(user, connection)

        for txn in transactions:
            try:
                # Skip if transaction already exists (check by date + amount + description)
                txn_date = datetime.strptime(txn["date"], "%Y-%m-%d").date()
                txn_amount_raw = Decimal(
                    str(txn["amount"])
                )  # Convert to Decimal for comparison
                txn_amount = abs(txn_amount_raw)  # Store absolute value for expense
                txn_description = txn.get("description", "")

                # Check for duplicates
                if self._is_duplicate_transaction(
                    user, txn_date, txn_amount, txn_description
                ):
                    continue

                # Only sync debit transactions (expenses)
                if txn_amount_raw < 0:  # Negative amount = debit/expense
                    self.expense_repository.create_expense(
                        user=user,
                        account=card_account,
                        category=None,  # Will need to be categorized later
                        description=txn_description,
                        amount=txn_amount,
                        date=txn_date,
                    )
                    synced_count += 1

            except Exception as e:
                logger.error(f"Error syncing transaction {txn.get('id')}: {str(e)}")
                continue

        logger.info(f"Synced {synced_count} transactions")
        return synced_count

    def _get_or_create_card_account(
        self, user: User, connection: TellerConnection
    ) -> CardAccount:
        """Get or create a CardAccount for the Teller connection."""
        account_name = f"{connection.institution_name} - {connection.account_name}"

        # Try to find existing card account
        cards = self.card_repository.get_by_user(user)
        for card in cards:
            if card.name == account_name:
                return card

        # Create new card account
        bank = self._map_institution_name(connection.institution_name)
        return self.card_repository.create_card_account(
            user=user, name=account_name, bank=bank
        )

    def _map_account_type(self, teller_type: str) -> str:
        """Map Teller account type to our account types."""
        type_mapping = {
            "depository": "checking",
            "credit": "checking",
            "loan": "checking",
            "investment": "investment",
        }
        return type_mapping.get(teller_type.lower(), "checking")

    def _map_institution_name(self, institution_name: str) -> str:
        """Map institution name to our supported entity names."""
        name_lower = institution_name.lower()
        if "bank of america" in name_lower or "boa" in name_lower:
            return "bank_of_america"
        elif "chase" in name_lower:
            return "chase"
        elif "citi" in name_lower:
            return "citibank"
        elif "marcus" in name_lower:
            return "marcus"
        else:
            return "other"
