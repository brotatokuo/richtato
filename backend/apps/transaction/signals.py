"""Signals for Transaction model to maintain account balance history."""

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from loguru import logger

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.transaction.models import Transaction


def recalculate_balance_for_date(
    account: FinancialAccount, target_date: date, current_balance: Decimal = None
) -> Decimal:
    """
    Recalculate and store the account balance at target_date.

    Uses the current account balance as an anchor and works backwards
    by subtracting transactions that occurred after target_date.

    Args:
        account: The financial account to recalculate
        target_date: The date to calculate balance for
        current_balance: Optional pre-fetched current balance (optimization)

    Returns:
        The calculated balance at target_date
    """
    if current_balance is None:
        # Refresh from DB to get latest balance
        account.refresh_from_db(fields=["balance"])
        current_balance = account.balance

    # Calculate net transactions AFTER target_date
    # These transactions haven't happened yet at target_date, so we subtract them
    credits_after = Transaction.objects.filter(
        account=account, date__gt=target_date, transaction_type="credit"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    debits_after = Transaction.objects.filter(
        account=account, date__gt=target_date, transaction_type="debit"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Balance at target_date = current balance - net change since then
    net_change_after = credits_after - debits_after
    balance_at_date = current_balance - net_change_after

    AccountBalanceHistory.objects.update_or_create(
        account=account, date=target_date, defaults={"balance": balance_at_date}
    )

    logger.debug(
        f"Updated balance history for account {account.id} ({account.name}) "
        f"on {target_date}: {balance_at_date}"
    )

    return balance_at_date


def update_balances_from_date(account: FinancialAccount, from_date: date) -> None:
    """
    Update balance history for all dates >= from_date that have transactions.

    This handles cascading updates when a transaction is modified or deleted,
    ensuring all subsequent balance snapshots remain accurate.

    Args:
        account: The financial account to update
        from_date: The starting date to update from
    """
    # Refresh account to get latest balance as our anchor
    account.refresh_from_db(fields=["balance"])
    current_balance = account.balance

    # Get all unique transaction dates >= from_date for this account
    affected_dates = (
        Transaction.objects.filter(account=account, date__gte=from_date)
        .values_list("date", flat=True)
        .distinct()
        .order_by("date")
    )

    # Also include any existing balance history dates that might need updating
    existing_history_dates = (
        AccountBalanceHistory.objects.filter(account=account, date__gte=from_date)
        .values_list("date", flat=True)
        .distinct()
    )

    # Combine and sort all dates that need recalculation
    all_dates = set(affected_dates) | set(existing_history_dates)

    for target_date in sorted(all_dates):
        recalculate_balance_for_date(account, target_date, current_balance)


@receiver(post_save, sender=Transaction)
def transaction_post_save(sender, instance: Transaction, created: bool, **kwargs):
    """
    Handle transaction creation or update.

    Updates balance history for the transaction date and all subsequent dates.
    Note: Account.balance is NOT updated here - it's the anchor from bank sync
    or manual entry, and balance history is derived from it.
    """
    account = instance.account
    transaction_date = instance.date

    logger.debug(
        f"Transaction {'created' if created else 'updated'}: "
        f"{instance.id} on {transaction_date} for account {account.name}"
    )

    # Update balance history from this date forward
    update_balances_from_date(account, transaction_date)


@receiver(post_delete, sender=Transaction)
def transaction_post_delete(sender, instance: Transaction, **kwargs):
    """
    Handle transaction deletion.

    Updates balance history for the deleted transaction's date and all subsequent dates.
    Note: Account.balance is NOT updated here - it's the anchor from bank sync
    or manual entry, and balance history is derived from it.
    """
    account = instance.account
    transaction_date = instance.date

    logger.debug(
        f"Transaction deleted: {instance.id} on {transaction_date} for account {account.name}"
    )

    # Update balance history from this date forward
    update_balances_from_date(account, transaction_date)

    # Clean up balance history entries for dates with no transactions
    # (only if there are no more transactions on that date)
    remaining_transactions = Transaction.objects.filter(
        account=account, date=transaction_date
    ).exists()

    if not remaining_transactions:
        # Remove the balance history entry for this date since there are no transactions
        AccountBalanceHistory.objects.filter(
            account=account, date=transaction_date
        ).delete()
        logger.debug(
            f"Removed balance history entry for account {account.id} on {transaction_date} "
            "(no remaining transactions)"
        )
