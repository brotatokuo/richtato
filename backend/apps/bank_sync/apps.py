"""App config for the legacy bank-sync vault.

The Playwright runner now lives entirely in the standalone ``bank-agent``
CLI (see ``scripts/bank_sync/``). Only the legacy models, encryption,
and the ``export_bank_sync_to_agent`` management command remain here so
existing users can migrate to the new agent.
"""

from django.apps import AppConfig


class BankSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bank_sync"
    verbose_name = "Bank Sync (legacy export only)"
