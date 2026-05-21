"""Long-lived container entrypoint.

Wraps :func:`scripts.automation.runner.run_all` in a daily schedule using the
``schedule`` library. Times are interpreted in the container's local timezone -
set ``TZ`` in the project ``.env`` (the docker-compose service inherits it) to
align with the operator's wall clock.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

import schedule
from loguru import logger

from scripts.automation.config import load_config
from scripts.automation.runner import run_all

POLL_INTERVAL_SECONDS = 30


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


def main() -> int:
    _configure_logging()
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
