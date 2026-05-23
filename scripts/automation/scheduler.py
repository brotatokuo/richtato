"""Long-lived container entrypoint.

In Phase 1 the scheduler operates in two modes:

* **DB mode (default when ``BANK_AUTOMATION_DB_MODE=1``):** every
  ``POLL_INTERVAL_SECONDS`` it asks the backend for the user's due
  ``BankConnection`` rows and drives any returned. The backend owns the
  schedule (per-cadence ``next_run_at``); the scheduler is just a worker.
* **Legacy mode:** wraps :func:`scripts.automation.runner.run_all` in a
  daily ``schedule`` job, kept for the original ``accounts.json`` path.

Times are interpreted in the container's local timezone — set ``TZ`` in the
project ``.env`` to align with the operator's wall clock.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

import schedule
from loguru import logger

from scripts.automation.config import load_config
from scripts.automation.errors import ConfigError
from scripts.automation.runner import run_all, run_db

POLL_INTERVAL_SECONDS = 30
# Default DB poll cadence. The runner's only blocking work happens *during* a
# poll, so a tighter cadence just makes manual "Sync now" feel faster — the
# bank is never hit until a connection's ``next_run_at`` is actually due.
DB_POLL_INTERVAL_SECONDS = int(os.environ.get("BANK_AUTOMATION_DB_POLL_SECONDS", "60"))


def _is_db_mode() -> bool:
    raw = os.environ.get("BANK_AUTOMATION_DB_MODE", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _configure_logging() -> None:
    config = load_config()
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    log_file = (
        config.logs_dir
        / f"scheduler-{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
    )
    logger.add(log_file, level="DEBUG", rotation="10 MB", retention="30 days")


def _job() -> None:
    logger.info("Daily run starting at {}", datetime.now().isoformat())
    try:
        failures = run_all()
    except Exception:
        logger.exception("run_all raised - scheduler will continue")
        return
    logger.info("Daily run finished with {} failures", failures)


def _db_loop() -> int:
    """Poll the backend for due connections forever."""

    config = load_config()
    logger.info(
        "Bank automation scheduler starting in DB mode (poll={}s, base_url={})",
        DB_POLL_INTERVAL_SECONDS,
        config.richtato_base_url,
    )
    while True:
        logger.debug("Polling for due bank connections...")
        try:
            failures = run_db(config)
            if failures:
                logger.warning("DB poll completed with {} failure(s)", failures)
        except ConfigError as exc:
            # Transient backend unavailability (refused connection, 5xx) and
            # operator misconfiguration (403, missing creds) both surface as
            # ConfigError. Log once on a single line so the scheduler isn't
            # buried under a 60-line traceback every poll.
            logger.warning("DB poll skipped: {}", exc)
        except Exception:
            logger.exception("DB poll raised unexpectedly - scheduler will continue")
        time.sleep(DB_POLL_INTERVAL_SECONDS)


def main() -> int:
    _configure_logging()

    if _is_db_mode():
        return _db_loop()

    config = load_config()

    logger.info(
        "Automation scheduler starting (TZ={}, RUN_TIME={}, enabled={})",
        os.environ.get("TZ", "unset"),
        config.run_time,
        ",".join(config.enabled_institutions) or "<none>",
    )

    try:
        schedule.every().day.at(config.run_time).do(_job)
    except schedule.ScheduleValueError as exc:
        logger.error("Invalid RUN_TIME={!r}: {}", config.run_time, exc)
        return 1

    next_run = schedule.next_run()
    if next_run is not None:
        logger.info("First scheduled run at {} (local time)", next_run.isoformat())

    while True:
        schedule.run_pending()
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
