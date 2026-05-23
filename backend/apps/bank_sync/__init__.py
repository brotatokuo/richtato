"""Legacy bank-sync vault — kept only for one-shot migration.

The active Playwright agent has moved to ``scripts/bank_sync/`` as an
independent host process. Only the legacy ``BankLogin`` / ``SyncedAccount``
models, their encryption envelope, and the
``export_bank_sync_to_agent`` management command remain here so users can
migrate their stored cookies to the new agent SQLite.
"""
