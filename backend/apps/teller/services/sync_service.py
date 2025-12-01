"""Sync service for fetching and mapping Teller transactions."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from apps.account.models import Account
from apps.account.repositories.account_repository import AccountRepository
from apps.expense.models import Expense
from apps.expense.repositories.expense_repository import ExpenseRepository
from apps.card.models import CardAccount
from apps.card.repositories.card_account_repository import CardAccountRepository
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
        self, connection: TellerConnection, days: int = 30
    ) -> Dict[str, any]:
        """
        Sync transactions from Teller for a specific connection.

        Args:
            connection: TellerConnection to sync
            days: Number of days to fetch transactions for (default 30)

        Returns:
            Dict with sync results including counts and errors
        """
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
            accounts = self.account_repository.filter_by_user(user)
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
                self.account_repository.update(
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
                new_account = self.account_repository.create(
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
                txn_amount = abs(Decimal(str(txn["amount"])))
                txn_description = txn.get("description", "")

                # Check for duplicates
                existing_expenses = self.expense_repository.filter_by_user(user)
                is_duplicate = False
                for exp in existing_expenses:
                    if (
                        exp.date == txn_date
                        and abs(exp.amount - txn_amount) < Decimal("0.01")
                        and exp.description == txn_description
                    ):
                        is_duplicate = True
                        break

                if is_duplicate:
                    continue

                # Only sync debit transactions (expenses)
                if txn["amount"] < 0:  # Negative amount = debit/expense
                    self.expense_repository.create(
                        user=user,
                        description=txn_description,
                        amount=txn_amount,
                        date=txn_date,
                        account_name=card_account,
                        category=None,  # Will need to be categorized later
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
        return self.card_repository.create(user=user, name=account_name, bank=bank)

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
