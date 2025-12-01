from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


class TellerClient:
    BASE_URL = "https://api.teller.io"

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

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Internal method to make authenticated GET requests."""
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, cert=self.cert, auth=self.auth, params=params)
        response.raise_for_status()
        return response.json()

    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Fetch all accounts associated with the access token.

        Returns:
            List of account objects containing details like id, name, balance, etc.
        """
        return self._get("/accounts")

    def get_transactions(
        self, account_id: str, count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch transactions for a specific account.

        Args:
            account_id: The ID of the account to fetch transactions for.
            count: Optional number of transactions to retrieve (default is API default).

        Returns:
            List of transaction objects.
        """
        params = {}
        if count is not None:
            params["count"] = count

        return self._get(f"/accounts/{account_id}/transactions", params=params)

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
