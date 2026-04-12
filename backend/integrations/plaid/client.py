"""Plaid API client implementation."""

import random
import time
from collections.abc import Generator
from typing import Any

import plaid
from loguru import logger
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from integrations.base import BaseBankingClient


class PlaidClient(BaseBankingClient):
    """
    Plaid API client implementation.

    Uses the official plaid-python SDK for API communication.
    Implements cursor-based transaction sync.
    """

    # Rate limiting settings - conservative for free tier APIs
    MAX_RETRIES = 8
    BASE_DELAY = 5.0  # Base delay in seconds for exponential backoff
    MAX_DELAY = 120.0  # Maximum delay between retries
    REQUEST_DELAY = 5.0  # Delay between normal requests to avoid rate limits
    BATCH_DELAY = 10.0  # Delay between pagination batches

    def __init__(
        self,
        client_id: str,
        secret: str,
        environment: str = "sandbox",
        access_token: str | None = None,
    ):
        """
        Initialize the Plaid API client.

        Args:
            client_id: Plaid client ID
            secret: Plaid secret key
            environment: Plaid environment (sandbox, development, production)
            access_token: Optional access token for an already-linked account
        """
        self.client_id = client_id
        self.secret = secret
        self.access_token = access_token
        self._last_request_time = 0.0

        # Configure Plaid client
        env_mapping = {
            "sandbox": plaid.Environment.Sandbox,
            "development": plaid.Environment.Development,
            "production": plaid.Environment.Production,
        }

        configuration = plaid.Configuration(
            host=env_mapping.get(environment, plaid.Environment.Sandbox),
            api_key={
                "clientId": client_id,
                "secret": secret,
            },
        )

        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def _wait_for_rate_limit(self):
        """Ensure minimum delay between requests with jitter."""
        elapsed = time.time() - self._last_request_time
        # Add 0-50% jitter to prevent synchronized requests
        jitter = random.uniform(0, self.REQUEST_DELAY * 0.5)
        delay_needed = self.REQUEST_DELAY + jitter
        if elapsed < delay_needed:
            time.sleep(delay_needed - elapsed)
        self._last_request_time = time.time()

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry logic."""
        for attempt in range(self.MAX_RETRIES):
            self._wait_for_rate_limit()
            try:
                return func(*args, **kwargs)
            except plaid.ApiException as e:
                if e.status == 429 and attempt < self.MAX_RETRIES - 1:
                    delay = min(self.BASE_DELAY * (2**attempt), self.MAX_DELAY)
                    # Add jitter to prevent synchronized retries
                    jitter = random.uniform(0, delay * 0.25)
                    delay = delay + jitter
                    logger.warning(
                        f"Rate limited by Plaid API. Waiting {delay:.1f}s before retry "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                    continue
                raise
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = min(self.BASE_DELAY * (2**attempt), self.MAX_DELAY)
                    # Add jitter to prevent synchronized retries
                    jitter = random.uniform(0, delay * 0.25)
                    delay = delay + jitter
                    logger.warning(
                        f"Request failed: {e}. Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                    continue
                raise

        raise Exception(f"Max retries ({self.MAX_RETRIES}) exceeded")

    def create_link_token(self, user_id: str, redirect_uri: str | None = None) -> str:
        """
        Create a Plaid Link token for initializing Link.

        Configures the token to request maximum historical transaction data
        (730 days = 2 years) instead of the default 90 days.

        Args:
            user_id: Unique identifier for the user
            redirect_uri: Optional redirect URI for OAuth flows

        Returns:
            Link token string
        """
        request_params = {
            "products": [Products("transactions")],
            "client_name": "Richtato",
            "country_codes": [CountryCode("US")],
            "language": "en",
            "user": LinkTokenCreateRequestUser(client_user_id=user_id),
            # Request maximum historical data (730 days = 2 years)
            "transactions": {"days_requested": 730},
        }

        if redirect_uri:
            request_params["redirect_uri"] = redirect_uri

        request = LinkTokenCreateRequest(**request_params)

        response = self._retry_with_backoff(self.client.link_token_create, request)
        return response["link_token"]

    def exchange_public_token(self, public_token: str) -> dict[str, str]:
        """
        Exchange a public token for an access token.

        Args:
            public_token: Public token from Plaid Link

        Returns:
            Dict with access_token and item_id
        """
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self._retry_with_backoff(self.client.item_public_token_exchange, request)
        return {
            "access_token": response["access_token"],
            "item_id": response["item_id"],
        }

    def get_accounts(self) -> list[dict[str, Any]]:
        """
        Fetch all accounts associated with the access token.

        Returns:
            List of normalized account objects.
        """
        if not self.access_token:
            raise ValueError("Access token is required to fetch accounts")

        request = AccountsGetRequest(access_token=self.access_token)
        response = self._retry_with_backoff(self.client.accounts_get, request)

        accounts = []
        for account in response["accounts"]:
            # Convert Plaid enum types to strings
            account_type = account["type"]
            account_subtype = account.get("subtype")

            # Plaid SDK returns enum objects, convert to string values
            if hasattr(account_type, "value"):
                account_type = account_type.value
            else:
                account_type = str(account_type)

            if account_subtype is not None:
                if hasattr(account_subtype, "value"):
                    account_subtype = account_subtype.value
                else:
                    account_subtype = str(account_subtype)
            else:
                account_subtype = ""

            # Normalize Plaid account structure to match expected format
            normalized = {
                "id": account["account_id"],
                "name": account["name"],
                "type": account_type,
                "subtype": account_subtype,
                "last_four": account.get("mask", ""),
                "balances": {
                    "ledger": account["balances"].get("current"),
                    "available": account["balances"].get("available"),
                },
                # Include original data for reference
                "_plaid_data": {
                    "official_name": account.get("official_name"),
                    "persistent_account_id": account.get("persistent_account_id"),
                },
            }
            accounts.append(normalized)

        logger.info(f"Fetched {len(accounts)} accounts from Plaid")
        return accounts

    def get_account_balance(self, account_id: str) -> dict[str, Any]:
        """
        Fetch account balance from Plaid.

        Args:
            account_id: The ID of the account to fetch balance for.

        Returns:
            Dictionary containing balance information.
        """
        if not self.access_token:
            raise ValueError("Access token is required to fetch balance")

        request = AccountsBalanceGetRequest(access_token=self.access_token)
        response = self._retry_with_backoff(self.client.accounts_balance_get, request)

        # Find the specific account
        for account in response["accounts"]:
            if account["account_id"] == account_id:
                return {
                    "account_id": account_id,
                    "ledger": account["balances"].get("current"),
                    "available": account["balances"].get("available"),
                }

        raise ValueError(f"Account {account_id} not found")

    def get_transactions(
        self,
        account_id: str,
        count: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        cursor: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Fetch transactions for a specific account using Plaid's sync API.

        Note: Plaid uses cursor-based sync rather than date-based fetching.
        The start_date/end_date parameters are used for filtering after fetch.

        Args:
            account_id: The ID of the account (used for filtering).
            count: Optional limit on transactions to return.
            start_date: Start date for filtering (YYYY-MM-DD).
            end_date: End date for filtering (YYYY-MM-DD).
            cursor: Optional cursor for pagination.

        Returns:
            List of normalized transaction objects.
        """
        if not self.access_token:
            raise ValueError("Access token is required to fetch transactions")

        request = TransactionsSyncRequest(
            access_token=self.access_token,
            cursor=cursor or "",
            count=count or 500,
        )

        response = self._retry_with_backoff(self.client.transactions_sync, request)

        transactions = []
        for txn in response.get("added", []):
            # Filter by account if specified
            if account_id and txn["account_id"] != account_id:
                continue

            # Normalize Plaid transaction to expected format
            # Note: Plaid amounts are positive for outflows, negative for inflows
            # We keep this convention in raw data, sync service will handle conversion
            normalized = {
                "id": txn["transaction_id"],
                "date": txn["date"],
                "amount": txn["amount"],  # Plaid: positive = debit, negative = credit
                "description": txn.get("name", ""),
                "merchant": {
                    "name": txn.get("merchant_name"),
                    "category": txn.get("personal_finance_category", {}).get("primary"),
                }
                if txn.get("merchant_name")
                else None,
                "type": txn.get("payment_channel", "other"),  # online, in_store, other
                "status": "pending" if txn.get("pending", False) else "posted",
                "details": {
                    "category": txn.get("personal_finance_category", {}),
                    "location": txn.get("location", {}),
                },
                # Include raw data for reference
                "_plaid_data": txn,
            }
            transactions.append(normalized)

        # Apply date filtering if specified
        if start_date or end_date:
            transactions = self.filter_transactions(transactions, start_date, end_date)

        # Store cursor for pagination
        self._last_cursor = response.get("next_cursor", "")
        self._has_more = response.get("has_more", False)

        return transactions

    def get_transactions_paginated(
        self,
        account_id: str,
        batch_size: int = 500,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Generator[list[dict[str, Any]], None, None]:
        """
        Fetch transactions in batches using Plaid's cursor-based sync.

        Args:
            account_id: The ID of the account to fetch transactions for.
            batch_size: Number of transactions per batch (max 500).
            start_date: Start date in 'YYYY-MM-DD' format (inclusive).
            end_date: End date in 'YYYY-MM-DD' format (inclusive).

        Yields:
            Batches of transaction objects (list of dicts).
        """
        if not self.access_token:
            raise ValueError("Access token is required to fetch transactions")

        cursor = ""
        batch_count = 0
        batch_size = min(batch_size, 500)

        while True:
            batch_count += 1

            request = TransactionsSyncRequest(
                access_token=self.access_token,
                cursor=cursor,
                count=batch_size,
            )

            response = self._retry_with_backoff(self.client.transactions_sync, request)

            # Process added transactions
            added = response.get("added", [])
            modified = response.get("modified", [])
            removed = response.get("removed", [])

            logger.info(
                f"Plaid sync batch {batch_count}: {len(added)} added, {len(modified)} modified, {len(removed)} removed"
            )

            # Combine and normalize transactions
            all_transactions = []
            for txn in added + modified:
                # Filter by account if specified
                if account_id and txn["account_id"] != account_id:
                    continue

                normalized = {
                    "id": txn["transaction_id"],
                    "date": txn["date"],
                    "amount": txn["amount"],
                    "description": txn.get("name", ""),
                    "merchant": {
                        "name": txn.get("merchant_name"),
                        "category": txn.get("personal_finance_category", {}).get("primary"),
                    }
                    if txn.get("merchant_name")
                    else None,
                    "type": txn.get("payment_channel", "other"),
                    "status": "pending" if txn.get("pending", False) else "posted",
                    "details": {
                        "category": txn.get("personal_finance_category", {}),
                        "location": txn.get("location", {}),
                    },
                    "_plaid_data": txn,
                    "_is_modified": txn in modified,
                }
                all_transactions.append(normalized)

            # Apply date filtering
            if start_date or end_date:
                all_transactions = self.filter_transactions(all_transactions, start_date, end_date)

            if all_transactions:
                yield all_transactions

            # Check if there are more transactions
            cursor = response.get("next_cursor", "")
            has_more = response.get("has_more", False)

            if not has_more or not cursor:
                break

            # Add delay between batches with jitter to avoid rate limits
            jitter = random.uniform(0, self.BATCH_DELAY * 0.3)
            time.sleep(self.BATCH_DELAY + jitter)

    def get_item_info(self) -> dict[str, Any]:
        """
        Get information about the connected Item (institution connection).

        Returns:
            Dict with item and institution information.
        """
        if not self.access_token:
            raise ValueError("Access token is required")

        from plaid.model.institutions_get_by_id_request import (
            InstitutionsGetByIdRequest,
        )
        from plaid.model.item_get_request import ItemGetRequest

        # Get item info
        item_request = ItemGetRequest(access_token=self.access_token)
        item_response = self._retry_with_backoff(self.client.item_get, item_request)

        item = item_response["item"]
        institution_id = item.get("institution_id")

        # Get institution info
        institution_name = "Unknown"
        if institution_id:
            try:
                inst_request = InstitutionsGetByIdRequest(
                    institution_id=institution_id,
                    country_codes=[CountryCode("US")],
                )
                inst_response = self._retry_with_backoff(self.client.institutions_get_by_id, inst_request)
                institution_name = inst_response["institution"]["name"]
            except Exception as e:
                logger.warning(f"Could not fetch institution info: {e}")

        return {
            "item_id": item.get("item_id"),
            "institution_id": institution_id,
            "institution_name": institution_name,
            "available_products": item.get("available_products", []),
            "billed_products": item.get("billed_products", []),
            "consent_expiration_time": item.get("consent_expiration_time"),
            "update_type": item.get("update_type"),
        }
