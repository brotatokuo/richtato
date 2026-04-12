"""Negate liability account balances to adopt negative-storage convention.

Previously credit card balances were stored as positive (e.g. owe $500 = balance 500).
New convention: liabilities stored negative (owe $500 = balance -500).
"""

from django.db import migrations
from django.db.models import F


def negate_liability_balances(apps, schema_editor):
    FinancialAccount = apps.get_model("financial_account", "FinancialAccount")
    AccountBalanceHistory = apps.get_model("financial_account", "AccountBalanceHistory")

    liability_ids = list(
        FinancialAccount.objects.filter(is_liability=True).values_list("id", flat=True)
    )
    if not liability_ids:
        return

    FinancialAccount.objects.filter(id__in=liability_ids).exclude(balance=0).update(
        balance=-F("balance")
    )
    AccountBalanceHistory.objects.filter(account_id__in=liability_ids).exclude(
        balance=0
    ).update(balance=-F("balance"))


def reverse_negate(apps, schema_editor):
    FinancialAccount = apps.get_model("financial_account", "FinancialAccount")
    AccountBalanceHistory = apps.get_model("financial_account", "AccountBalanceHistory")

    liability_ids = list(
        FinancialAccount.objects.filter(is_liability=True).values_list("id", flat=True)
    )
    if not liability_ids:
        return

    FinancialAccount.objects.filter(id__in=liability_ids).exclude(balance=0).update(
        balance=-F("balance")
    )
    AccountBalanceHistory.objects.filter(account_id__in=liability_ids).exclude(
        balance=0
    ).update(balance=-F("balance"))


class Migration(migrations.Migration):

    dependencies = [
        ("financial_account", "0007_alter_financialaccount_sync_source"),
    ]

    operations = [
        migrations.RunPython(negate_liability_balances, reverse_negate),
    ]
