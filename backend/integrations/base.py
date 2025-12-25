"""Abstract base class for banking provider clients."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional


class BaseBankingClient(ABC):
    """
    Abstract base class defining the common interface for banking provider clients.

    All provider implementations (Plaid, etc.) should implement this interface
    to ensure consistent behavior across the application.
    """

    @abstractmethod
    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Fetch all accounts associated with the access token.

        Returns:
            List of account objects containing normalized fields:
            - id: External account ID
            - name: Account name
            - type: Account type (depository, credit, etc.)
            - subtype: Account subtype (checking, savings, credit_card, etc.)
            - last_four: Last 4 digits of account number
            - balances: Dict with 'ledger' and 'available' balance values
        """
        pass

    @abstractmethod
    def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Fetch account balance.

        Args:
            account_id: The ID of the account to fetch balance for.

        Returns:
            Dictionary containing balance information:
            - account_id: The account ID
            - ledger: Posted transactions balance (string or Decimal)
            - available: Available to spend balance (string or Decimal)
        """
        pass

    @abstractmethod
    def get_transactions(
        self,
        account_id: str,
        count: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Fetch transactions for a specific account.

        Args:
            account_id: The ID of the account to fetch transactions for.
            count: Optional number of transactions to retrieve.
            start_date: Start date in 'YYYY-MM-DD' format (inclusive).
            end_date: End date in 'YYYY-MM-DD' format (inclusive).
            **kwargs: Provider-specific parameters (e.g., cursor for Plaid).

        Returns:
            List of transaction objects with normalized fields:
            - id: External transaction ID
            - date: Transaction date (YYYY-MM-DD)
            - amount: Transaction amount (positive for credits, negative for debits)
            - description: Transaction description
            - merchant: Optional merchant info dict
            - type: Transaction type (ach, card, wire, etc.)
            - status: posted or pending
        """
        pass

    @abstractmethod
    def get_transactions_paginated(
        self,
        account_id: str,
        batch_size: int = 500,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Fetch transactions in batches using pagination.

        This method yields batches of transactions, automatically handling pagination.
        It will continue fetching until no more transactions are available.

        Args:
            account_id: The ID of the account to fetch transactions for.
            batch_size: Number of transactions per batch.
            start_date: Start date in 'YYYY-MM-DD' format (inclusive).
            end_date: End date in 'YYYY-MM-DD' format (inclusive).

        Yields:
            Batches of transaction objects (list of dicts).
        """
        pass

    def filter_transactions(
        self,
        transactions: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of transactions by date range.

        Default implementation that can be overridden by subclasses if needed.

        Args:
            transactions: List of transaction objects to filter.
            start_date: Start date string in 'YYYY-MM-DD' format (inclusive).
            end_date: End date string in 'YYYY-MM-DD' format (inclusive).

        Returns:
            Filtered list of transaction objects.
        """
        from datetime import datetime

        if not start_date and not end_date:
            return transactions

        filtered = []

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
