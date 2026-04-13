"""Signals for Transaction model to maintain account balance and history.

When a transaction is created, updated, or deleted, these signals:
1. Adjust FinancialAccount.balance (the anchor) to reflect the change
2. Recalculate AccountBalanceHistory entries from that anchor
"""

from datetime import date
from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.signals import post_delete, post_save, pre_save
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
        account.refresh_from_db(fields=["balance"])
        current_balance = account.balance

    credits_after = Transaction.objects.filter(
        account=account, date__gt=target_date, transaction_type="credit"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    debits_after = Transaction.objects.filter(
        account=account, date__gt=target_date, transaction_type="debit"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    net_change_after = credits_after - debits_after
    balance_at_date = current_balance - net_change_after

    AccountBalanceHistory.objects.update_or_create(
        account=account,
        date=target_date,
        defaults={"balance": balance_at_date, "source": "transaction"},
    )

    logger.debug(
        f"Updated balance history for account {account.id} ({account.name}) on {target_date}: {balance_at_date}"
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
    account.refresh_from_db(fields=["balance"])
    current_balance = account.balance

    affected_dates = (
        Transaction.objects.filter(account=account, date__gte=from_date)
        .values_list("date", flat=True)
        .distinct()
        .order_by("date")
    )

    existing_history_dates = (
        AccountBalanceHistory.objects.filter(account=account, date__gte=from_date)
        .values_list("date", flat=True)
        .distinct()
    )

    all_dates = set(affected_dates) | set(existing_history_dates)

    for target_date in sorted(all_dates):
        recalculate_balance_for_date(account, target_date, current_balance)


@receiver(pre_save, sender=Transaction)
def transaction_pre_save(sender, instance: Transaction, **kwargs):
    """Capture old values before update so post_save can compute the delta."""
    if instance.pk:
        try:
            old = Transaction.objects.get(pk=instance.pk)
            instance._old_signed_amount = old.signed_amount
            instance._old_date = old.date
            instance._old_account_id = old.account_id
        except Transaction.DoesNotExist:
            pass


@receiver(post_save, sender=Transaction)
def transaction_post_save(sender, instance: Transaction, created: bool, **kwargs):
    """
    After a transaction is created or updated:
    1. Adjust the account balance anchor so it stays current.
    2. Recalculate balance history from the affected date forward.
    """
    account = instance.account

    if created:
        FinancialAccount.objects.filter(pk=account.pk).update(balance=F("balance") + instance.signed_amount)
    else:
        old_signed = getattr(instance, "_old_signed_amount", Decimal("0"))
        delta = instance.signed_amount - old_signed
        if delta:
            FinancialAccount.objects.filter(pk=account.pk).update(balance=F("balance") + delta)

    account.refresh_from_db(fields=["balance"])

    logger.debug(
        f"Transaction {'created' if created else 'updated'}: "
        f"{instance.id} on {instance.date} for account {account.name} "
        f"(balance now {account.balance})"
    )

    old_date = getattr(instance, "_old_date", None)
    if not created and old_date and old_date != instance.date:
        update_balances_from_date(account, min(old_date, instance.date))

        # Clean up orphaned history entries on the old date
        has_remaining = Transaction.objects.filter(account=account, date=old_date).exists()
        if not has_remaining:
            AccountBalanceHistory.objects.filter(account=account, date=old_date).delete()
    else:
        update_balances_from_date(account, instance.date)


@receiver(post_delete, sender=Transaction)
def transaction_post_delete(sender, instance: Transaction, **kwargs):
    """
    After a transaction is deleted:
    1. Reverse its effect on the account balance anchor.
    2. Recalculate balance history from the affected date forward.
    3. Remove orphaned history entries for dates with no remaining transactions.
    """
    account = instance.account
    transaction_date = instance.date

    FinancialAccount.objects.filter(pk=account.pk).update(balance=F("balance") - instance.signed_amount)
    account.refresh_from_db(fields=["balance"])

    logger.debug(
        f"Transaction deleted: {instance.id} on {transaction_date} "
        f"for account {account.name} (balance now {account.balance})"
    )

    update_balances_from_date(account, transaction_date)

    remaining_transactions = Transaction.objects.filter(account=account, date=transaction_date).exists()

    if not remaining_transactions:
        AccountBalanceHistory.objects.filter(account=account, date=transaction_date).delete()
        logger.debug(
            f"Removed balance history entry for account {account.id} on {transaction_date} (no remaining transactions)"
        )
