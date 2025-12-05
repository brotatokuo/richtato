import time
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

import requests
from loguru import logger


class TellerClient:
    BASE_URL = "https://api.teller.io"

    # Rate limiting settings
    MAX_RETRIES = 5
    BASE_DELAY = 2.0  # Base delay in seconds
    MAX_DELAY = 60.0  # Maximum delay between retries
    REQUEST_DELAY = 0.5  # Delay between normal requests to avoid rate limits

    def __init__(self, cert_path: str, key_path: str, access_token: str):
        """
        Initialize the Teller API client.

        Args:
            cert_path: Path to the client certificate file (.pem)
            key_path: Path to the private key file (.pem)
            access_token: The access token for the connected account
        """
        self.cert = (cert_path, key_path)
        self.auth = (access_token, "")
        self._last_request_time = 0.0

    def _wait_for_rate_limit(self):
        """Ensure minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Internal method to make authenticated GET requests with retry logic."""
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            self._wait_for_rate_limit()

            try:
                response = requests.get(
                    url, cert=self.cert, auth=self.auth, params=params
                )

                if response.status_code == 429:
                    # Rate limited - extract retry-after or use exponential backoff
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        delay = float(retry_after)
                    else:
                        delay = min(self.BASE_DELAY * (2**attempt), self.MAX_DELAY)

                    logger.warning(
                        f"Rate limited by Teller API. Waiting {delay:.1f}s before retry "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if response.status_code == 429 and attempt < self.MAX_RETRIES - 1:
                    continue  # Already handled above, but just in case
                raise
            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = min(self.BASE_DELAY * (2**attempt), self.MAX_DELAY)
                    logger.warning(
                        f"Request failed: {e}. Retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                    continue
                raise

        raise requests.exceptions.HTTPError(
            f"Max retries ({self.MAX_RETRIES}) exceeded for {url}"
        )

    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Fetch all accounts associated with the access token.

        Returns:
            List of account objects containing details like id, name, balance, etc.
        """
        return self._get("/accounts")

    def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Fetch account balance from Teller.

        Args:
            account_id: The ID of the account to fetch balance for.

        Returns:
            Dictionary containing balance information:
            - account_id: The account ID
            - ledger: Posted transactions balance (string)
            - available: Available to spend balance (string)
        """
        return self._get(f"/accounts/{account_id}/balances")

    def get_transactions(
        self,
        account_id: str,
        count: Optional[int] = None,
        from_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch transactions for a specific account.

        Args:
            account_id: The ID of the account to fetch transactions for.
            count: Optional number of transactions to retrieve (default is API default, max 500).
            from_id: Transaction ID to start pagination from (returns older transactions).
            start_date: Start date in 'YYYY-MM-DD' format (inclusive).
            end_date: End date in 'YYYY-MM-DD' format (inclusive).

        Returns:
            List of transaction objects.
        """
        params = {}
        if count is not None:
            params["count"] = count
        if from_id is not None:
            params["from_id"] = from_id
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date

        return self._get(f"/accounts/{account_id}/transactions", params=params)

    def get_transactions_paginated(
        self,
        account_id: str,
        batch_size: int = 500,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Fetch transactions in batches using pagination.

        This method yields batches of transactions, automatically handling pagination
        using the from_id parameter. It will continue fetching until no more
        transactions are available.

        Includes rate limiting protection with delays between batch requests.

        Args:
            account_id: The ID of the account to fetch transactions for.
            batch_size: Number of transactions per batch (max 500).
            start_date: Start date in 'YYYY-MM-DD' format (inclusive).
            end_date: End date in 'YYYY-MM-DD' format (inclusive).

        Yields:
            Batches of transaction objects (list of dicts).
        """
        from_id = None
        batch_size = min(batch_size, 500)  # Enforce API maximum
        batch_count = 0

        while True:
            # Add extra delay between pagination requests to avoid rate limits
            if batch_count > 0:
                time.sleep(1.0)  # 1 second between batches

            batch_count += 1

            # Fetch a batch of transactions
            batch = self.get_transactions(
                account_id=account_id,
                count=batch_size,
                from_id=from_id,
                start_date=start_date,
                end_date=end_date,
            )

            # If no transactions returned, we're done
            if not batch:
                break

            yield batch

            # If we got fewer transactions than requested, we've reached the end
            if len(batch) < batch_size:
                break

            # Get the ID of the last (oldest) transaction for pagination
            from_id = batch[-1].get("id")
            if not from_id:
                break

    def filter_transactions(
        self,
        transactions: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of transactions by date range.

        Args:
            transactions: List of transaction objects to filter.
            start_date: Start date string in 'YYYY-MM-DD' format (inclusive).
            end_date: End date string in 'YYYY-MM-DD' format (inclusive).

        Returns:
            Filtered list of transaction objects.
        """
        if not start_date and not end_date:
            return transactions

        filtered = []

        # Parse dates for comparison
        start_dt = (
            datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        )
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        for txn in transactions:
            txn_date_str = txn.get("date")
            if not txn_date_str:
                continue

            txn_date = datetime.strptime(txn_date_str, "%Y-%m-%d").date()

            if start_dt and txn_date < start_dt:
                continue
            if end_dt and txn_date > end_dt:
                continue

            filtered.append(txn)

        return filtered
