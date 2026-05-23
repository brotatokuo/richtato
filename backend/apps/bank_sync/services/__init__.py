"""Bank sync service layer.

Three thin orchestrators in this package:

* :mod:`session_service` handles per-user envelope encryption of the
  Playwright ``storage_state`` blob.
* :mod:`login_service` owns ``BankLogin`` lifecycle: create, update,
  activate after capture, bind synced accounts.
* :mod:`run_service` enqueues / leases / completes ``SyncRun`` rows for the
  agent.
"""
