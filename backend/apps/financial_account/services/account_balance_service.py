"""Service for account balance tracking."""

from datetime import date
from decimal import Decimal

from loguru import logger

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)


class AccountBalanceService:
    """Service for tracking and managing account balances."""

    def __init__(self):
        self.account_repository = FinancialAccountRepository()

    def update_balance(
        self, account: FinancialAccount, new_balance: Decimal, balance_date: date = None
    ) -> FinancialAccount:
        """Set an account to a specific balance by creating an adjustment transaction.

        Computes the difference between current and desired balance, then
        creates a Balance Adjustment transaction. The transaction signal
        handles updating the anchor and history.

        Returns:
            Updated account (refreshed from DB)
        """
        from apps.transaction.models import Transaction

        if balance_date is None:
            balance_date = date.today()

        account.refresh_from_db(fields=["balance"])
        difference = new_balance - account.balance

        if difference != Decimal("0"):
            if difference > 0:
                txn_type = "credit"
                amount = difference
            else:
                txn_type = "debit"
                amount = abs(difference)

            Transaction.objects.create(
                user=account.user,
                account=account,
                date=balance_date,
                amount=amount,
                transaction_type=txn_type,
                description="Balance Adjustment",
                sync_source="manual",
                status="reconciled",
            )

        account.refresh_from_db()

        logger.info(
            f"Adjusted balance for account {account.id} ({account.name}) "
            f"to {new_balance} on {balance_date} (delta: {difference})"
        )

        return account

    def get_balance_history(
        self,
        account: FinancialAccount,
        start_date: date = None,
        end_date: date = None,
    ) -> list[AccountBalanceHistory]:
        """
        Get balance history for an account.

        Args:
            account: Account to get history for
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of balance history records
        """
        return self.account_repository.get_balance_history(account, start_date, end_date)

    def get_balance_trend(self, account: FinancialAccount) -> dict[str, any]:
        """Return all balance history for an account.

        Balances are stored with correct sign (negative for liabilities),
        so no sign-flipping is needed here.
        """
        history = list(AccountBalanceHistory.objects.filter(account=account).order_by("date"))

        if not history:
            return {
                "current_balance": account.balance,
                "starting_balance": account.balance,
                "change": Decimal("0"),
                "change_percent": Decimal("0"),
                "data_points": [],
            }

        starting_balance = history[0].balance
        current_balance = account.balance

        change = current_balance - starting_balance
        change_percent = (change / starting_balance * 100) if starting_balance != 0 else Decimal("0")

        data_points = [{"date": str(h.date), "balance": float(h.balance)} for h in history]

        return {
            "current_balance": current_balance,
            "starting_balance": starting_balance,
            "change": change,
            "change_percent": change_percent,
            "data_points": data_points,
        }
