"""Bulk transaction persistence helpers for statement import."""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save

from apps.financial_account.models import FinancialAccount
from apps.transaction.models import Transaction, TransactionCategory
from apps.transaction.signals import transaction_post_save, update_balances_from_date


@contextmanager
def suppress_transaction_balance_signals():
    """Disable per-transaction balance signals during bulk inserts."""
    post_save.disconnect(transaction_post_save, sender=Transaction)
    try:
        yield
    finally:
        post_save.connect(transaction_post_save, sender=Transaction)


def bulk_create_import_transactions(
    account: FinancialAccount,
    transactions: list[Transaction],
) -> int:
    """Insert imported transactions and apply balance side effects once."""
    if not transactions:
        return 0

    uncategorized = TransactionCategory.get_uncategorized_for_user(account.user)
    for txn in transactions:
        if txn.category_id is None:
            txn.category = uncategorized
        txn.categorization_status = "uncategorized"

    net_signed = sum((txn.signed_amount for txn in transactions), Decimal("0"))
    min_date = min(txn.date for txn in transactions)

    with suppress_transaction_balance_signals():
        with transaction.atomic():
            Transaction.objects.bulk_create(transactions, batch_size=500)
            if net_signed:
                FinancialAccount.objects.filter(pk=account.pk).update(balance=F("balance") + net_signed)

    account.refresh_from_db(fields=["balance"])
    update_balances_from_date(account, min_date)
    return len(transactions)
