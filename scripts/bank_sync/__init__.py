"""Standalone host-side bank-agent.

The agent has no runtime dependency on the Richtato Docker stack. It
keeps its own Fernet-encrypted SQLite vault under
``local_data/bank-agent/agent.db`` for bank logins, per-account
activity URLs, and a poll schedule; downloaded statements are written
directly into each account's configured ``storage_uri`` directory.

The Richtato backend independently scans those directories via
``python manage.py scan_statement_storage`` to discover and import the
files.

Bank passwords never enter this code path: sign-in always happens in a
headed Chromium window that the user drives manually, and only
Playwright ``storage_state`` is captured.
"""
