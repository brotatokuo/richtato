"""Service for account balance tracking."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from loguru import logger

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.transaction.models import Transaction

BALANCE_ON_DATE_ACCOUNT_TYPES = frozenset({"checking", "savings", "investment"})


@dataclass
class BalanceReconciliationResult:
    """Result of reconciling a user-entered balance against transaction history."""

    account: FinancialAccount
    computed_balance: Decimal
    adjustment: Decimal
    adjustment_transaction: Transaction | None


def compute_balance_at_date(
    account: FinancialAccount, target_date: date, current_balance: Decimal | None = None
) -> Decimal:
    """Compute account balance at target_date from the anchor and later transactions."""
    if current_balance is None:
        account.refresh_from_db(fields=["balance"])
        current_balance = account.balance

    credits_after = Transaction.objects.filter(
        account=account, date__gt=target_date, transaction_type="credit"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    debits_after = Transaction.objects.filter(
        account=account, date__gt=target_date, transaction_type="debit"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    net_change_after = credits_after - debits_after
    return current_balance - net_change_after


class AccountBalanceService:
    """Service for tracking and managing account balances."""

    def __init__(self):
        self.account_repository = FinancialAccountRepository()

    def update_balance(
        self, account: FinancialAccount, new_balance: Decimal, balance_date: date = None
    ) -> BalanceReconciliationResult:
        """Reconcile account balance on a date via a Balance Adjustment transaction.

        Computes the balance implied by existing transactions at the target date,
        then creates an adjustment transaction for any difference. Transaction
        signals update the anchor balance and history.
        """
        if balance_date is None:
            balance_date = date.today()

        account.refresh_from_db(fields=["balance"])
        computed_balance = compute_balance_at_date(account, balance_date)
        difference = new_balance - computed_balance
        adjustment_transaction = None

        if difference != Decimal("0"):
            if difference > 0:
                txn_type = "credit"
                amount = difference
            else:
                txn_type = "debit"
                amount = abs(difference)

            adjustment_transaction = Transaction.objects.create(
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
            f"to {new_balance} on {balance_date} (computed: {computed_balance}, delta: {difference})"
        )

        return BalanceReconciliationResult(
            account=account,
            computed_balance=computed_balance,
            adjustment=difference,
            adjustment_transaction=adjustment_transaction,
        )

    def set_balance_snapshot(
        self,
        account: FinancialAccount,
        new_balance: Decimal,
        balance_date: date = None,
        source: str = "manual",
    ) -> FinancialAccount:
        """Set absolute balance and overwrite/create history for the date.

        Internal-only snapshot write that bypasses transactions. Prefer
        update_balance() for user-facing reconciliation flows.
        """
        updated_account = self.account_repository.update_balance(
            account=account,
            balance=new_balance,
            balance_date=balance_date,
            source=source,
        )

        logger.info(
            f"Set balance snapshot for account {updated_account.id} ({updated_account.name}) "
            f"to {new_balance} on {balance_date or date.today()}"
        )

        return updated_account

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
