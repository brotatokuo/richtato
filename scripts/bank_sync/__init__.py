"""Bank-sync Playwright agent.

The agent polls Richtato's ``/api/v1/bank-sync/runner/due-tasks/`` endpoint
on a fixed interval. Each leased task is dispatched on its ``task_kind``:

* ``interactive_login`` — pops a headed Chromium window so the user can
  sign in. The agent captures the resulting ``storage_state`` plus a list
  of discovered bank-side accounts and posts both back.
* ``scheduled_download`` / ``manual_download`` — reuses the stored
  ``storage_state`` headless to download per-account statements, then
  POSTs them to ``/api/v1/accounts/import-statement/``.

Bank passwords never enter this code path.
"""
