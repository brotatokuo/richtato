"""Per-run orchestrator: loop institutions, download, import, alert.

Can be invoked directly (``python -m scripts.automation.runner``) for ad-hoc
runs or from :mod:`scripts.automation.scheduler` for the daily timer.
"""

from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from loguru import logger
from playwright.sync_api import (
    BrowserContext,
    Download,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from scripts.automation.config import (
    AutomationConfig,
    SUPPORTED_INSTITUTIONS,
    load_config,
)
from scripts.automation.errors import (
    AutomationError,
    DomBroken,
    ErrorKind,
    SessionExpired,
)
from scripts.automation.importer import submit_statement
from scripts.automation.institutions import get_adapter
from scripts.automation.institutions.base import InstitutionAdapter
from scripts.automation.notifier import Notifier
from scripts.automation.state import RunState, load_state, save_state

DEFAULT_VIEWPORT = {"width": 1280, "height": 800}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_LOCALE = "en-US"
DEFAULT_TIMEZONE_ID = "America/Los_Angeles"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the daily statement downloader once."
    )
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        metavar="INSTITUTION",
        help="Limit the run to this institution. Repeat to include more.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Override AUTOMATION_HEADLESS and launch a visible browser (debugging only; requires a display).",
    )
    return parser.parse_args(argv)


def _stealth_apply(context: BrowserContext) -> None:
    """Apply playwright-stealth to ``context`` if the package is installed.

    Stealth tweaks reduce trivial headless detection (navigator.webdriver,
    plugin shims, etc.). Failure is non-fatal; we log and continue.
    """

    try:
        from playwright_stealth import stealth_sync  # type: ignore[import-not-found]
    except ImportError:
        logger.debug("playwright_stealth not installed; running without stealth tweaks")
        return

    for page in context.pages:
        try:
            stealth_sync(page)
        except Exception as exc:  # pragma: no cover - best-effort
            logger.warning("stealth_sync failed: {}", exc)


@contextmanager
def _browser_context(
    config: AutomationConfig,
    storage_state_path: Path,
    headed_override: bool,
) -> Iterator[BrowserContext]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=not headed_override and config.headless
        )
        context = browser.new_context(
            storage_state=str(storage_state_path),
            user_agent=DEFAULT_USER_AGENT,
            viewport=DEFAULT_VIEWPORT,
            locale=DEFAULT_LOCALE,
            timezone_id=config.run_timezone or DEFAULT_TIMEZONE_ID,
            accept_downloads=True,
        )
        _stealth_apply(context)
        try:
            yield context
        finally:
            context.close()
            browser.close()


def _save_download(download: Download, downloads_dir: Path) -> Path:
    downloads_dir.mkdir(parents=True, exist_ok=True)
    suggested = download.suggested_filename or "statement.csv"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    target = downloads_dir / f"{timestamp}_{suggested}"
    download.save_as(target)
    return target


def _drive_one_institution(
    adapter: InstitutionAdapter,
    config: AutomationConfig,
    headed_override: bool,
) -> Path:
    """Run the browser flow for a single institution and return the saved file path."""

    storage_state_path = config.storage_state_path(adapter.SLUG)
    if not storage_state_path.exists():
        raise SessionExpired(
            f"No storage state file at {storage_state_path}. Bootstrap this institution first."
        )

    with _browser_context(config, storage_state_path, headed_override) as context:
        page: Page = context.new_page()
        page.set_default_timeout(adapter.nav_timeout_ms)
        try:
            page.goto(adapter.URL, wait_until="domcontentloaded")
        except PlaywrightTimeoutError as exc:
            raise DomBroken(f"Timed out loading {adapter.URL}: {exc}") from exc

        if not adapter.is_session_valid(page):
            raise SessionExpired(f"Session check failed for {adapter.SLUG}")

        adapter.navigate_to_export(page)
        download = adapter.trigger_download(page)
        return _save_download(download, config.downloads_dir(adapter.SLUG))


def _check_stale(config: AutomationConfig, state: RunState, notifier: Notifier) -> None:
    """Emit stale alerts for institutions whose last success is older than the threshold."""

    threshold = timedelta(days=config.stale_threshold_days)
    now = datetime.now(timezone.utc)
    for slug in config.enabled_institutions:
        entry = state.get(slug)
        if entry.last_success is None:
            continue
        try:
            last = datetime.fromisoformat(entry.last_success)
        except ValueError:
            continue
        if now - last > threshold and entry.consecutive_failures == 0:
            notifier.record_stale(slug, entry)


def _run_institution(
    slug: str,
    config: AutomationConfig,
    state: RunState,
    notifier: Notifier,
    headed_override: bool,
) -> bool:
    """Run one institution end-to-end. Returns True on success."""

    logger.info("[{}] starting", slug)
    try:
        adapter = get_adapter(slug)
    except (LookupError, TypeError) as exc:
        notifier.record_failure(slug, ErrorKind.CONFIG, str(exc), state.get(slug), exc)
        state.record_failure(slug, str(exc))
        return False

    try:
        downloaded_path = _drive_one_institution(adapter, config, headed_override)
    except AutomationError as exc:
        logger.error("[{}] {}: {}", slug, exc.kind.value, exc.message)
        notifier.record_failure(slug, exc.kind, exc.message, state.get(slug), exc)
        state.record_failure(slug, exc.message)
        return False
    except PlaywrightTimeoutError as exc:
        message = f"Playwright timeout: {exc}"
        logger.error("[{}] dom_broken: {}", slug, message)
        notifier.record_failure(
            slug, ErrorKind.DOM_BROKEN, message, state.get(slug), exc
        )
        state.record_failure(slug, message)
        return False
    except Exception as exc:
        logger.exception("[{}] unexpected error", slug)
        notifier.record_failure(slug, ErrorKind.UNKNOWN, str(exc), state.get(slug), exc)
        state.record_failure(slug, str(exc))
        return False

    try:
        submit_statement(config, slug, downloaded_path)
    except AutomationError as exc:
        logger.error("[{}] import_rejected: {}", slug, exc.message)
        notifier.record_failure(slug, exc.kind, exc.message, state.get(slug), exc)
        state.record_failure(slug, exc.message)
        return False
    except Exception as exc:
        logger.exception("[{}] unexpected import error", slug)
        notifier.record_failure(slug, ErrorKind.UNKNOWN, str(exc), state.get(slug), exc)
        state.record_failure(slug, str(exc))
        return False

    state.record_success(slug, downloaded_path)
    logger.info("[{}] success ({})", slug, downloaded_path.name)
    return True


def _resolve_run_list(
    config: AutomationConfig, requested: list[str] | None
) -> list[str]:
    if requested:
        unknown = [slug for slug in requested if slug not in SUPPORTED_INSTITUTIONS]
        if unknown:
            raise SystemExit(f"Unknown institution(s): {', '.join(unknown)}")
        return list(requested)
    return list(config.enabled_institutions)


def run_all(
    config: AutomationConfig | None = None,
    only: list[str] | None = None,
    headed_override: bool = False,
) -> int:
    """Execute one full pass. Returns the number of failures."""

    config = config or load_config()
    institutions = _resolve_run_list(config, only)
    if not institutions:
        logger.warning("No institutions enabled; nothing to do.")
        return 0

    state = load_state(config.state_file)
    notifier = Notifier(config)

    failures = 0
    for slug in institutions:
        if not _run_institution(slug, config, state, notifier, headed_override):
            failures += 1

    _check_stale(config, state, notifier)
    save_state(state, config.state_file)
    notifier.flush()

    logger.info(
        "Run complete: {} succeeded, {} failed", len(institutions) - failures, failures
    )
    return failures


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config()

    logger.remove()
    logger.add(sys.stderr, level="INFO")
    log_file = (
        config.logs_dir / f"runner-{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
    )
    logger.add(log_file, level="DEBUG", rotation="10 MB", retention="30 days")

    return run_all(config, only=args.only, headed_override=args.headed)


if __name__ == "__main__":
    raise SystemExit(main())
