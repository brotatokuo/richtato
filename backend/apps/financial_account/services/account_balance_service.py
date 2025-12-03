"""Service for account balance tracking."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from loguru import logger


class AccountBalanceService:
    """Service for tracking and managing account balances."""

    def __init__(self):
        self.account_repository = FinancialAccountRepository()

    def update_balance(
        self, account: FinancialAccount, new_balance: Decimal, balance_date: date = None
    ) -> FinancialAccount:
        """
        Update account balance and record history.

        Args:
            account: Account to update
            new_balance: New balance amount
            balance_date: Date of the balance (defaults to today)

        Returns:
            Updated account
        """
        if balance_date is None:
            balance_date = date.today()

        account = self.account_repository.update_balance(
            account, new_balance, balance_date
        )

        logger.info(
            f"Updated balance for account {account.id} ({account.name}) "
            f"to {new_balance} on {balance_date}"
        )

        return account

    def get_balance_history(
        self,
        account: FinancialAccount,
        start_date: date = None,
        end_date: date = None,
    ) -> List[AccountBalanceHistory]:
        """
        Get balance history for an account.

        Args:
            account: Account to get history for
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of balance history records
        """
        return self.account_repository.get_balance_history(
            account, start_date, end_date
        )

    def get_balance_trend(
        self, account: FinancialAccount, days: int = 30
    ) -> Dict[str, any]:
        """
        Get balance trend over specified number of days.

        Args:
            account: Account to analyze
            days: Number of days to look back

        Returns:
            Dict with trend data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        history = self.get_balance_history(account, start_date, end_date)

        if not history:
            return {
                "current_balance": account.balance,
                "starting_balance": account.balance,
                "change": Decimal("0"),
                "change_percent": Decimal("0"),
                "data_points": [],
            }

        starting_balance = history[-1].balance if history else account.balance
        change = account.balance - starting_balance
        change_percent = (
            (change / starting_balance * 100) if starting_balance != 0 else Decimal("0")
        )

        return {
            "current_balance": account.balance,
            "starting_balance": starting_balance,
            "change": change,
            "change_percent": change_percent,
            "data_points": [
                {"date": str(h.date), "balance": float(h.balance)} for h in history
            ],
        }
