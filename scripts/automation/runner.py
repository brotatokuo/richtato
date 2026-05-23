"""Per-run orchestrator: loop institutions, download, import, alert.

Two execution paths coexist:

* **Legacy institution path** (``--only <institution>``): one slug owns one
  storage state, one URL, and one Richtato account ID. Used by Chase, Marcus,
  and the original BoFA adapter. Downloads then auto-imports to Richtato.
* **Multi-account path** (``--account <slug>`` / ``--login <id>``): driven by
  ``local_data/automation/accounts.json``. Each ``AutomationAccount`` brings
  its own activity URL but multiple accounts share one ``LoginSession`` so a
  single browser context downloads all accounts under that login. This path
  is download-only (no auto-import).

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
    AutomationAccount,
    AutomationConfig,
    LoginSession,
    SUPPORTED_INSTITUTIONS,
    load_config,
)
from scripts.automation.db_loader import (
    DBAccount,
    DBConnection,
    fetch_due_connections,
    post_run_outcome,
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
from scripts.automation.institutions.bofa_account import BofaAccountAdapter
from scripts.automation.institutions.multi_account import get_account_adapter
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
        help=(
            "Legacy: limit the run to this institution slug. Repeat to include more. "
            "Uses the single-account-per-institution flow with auto-import."
        ),
    )
    parser.add_argument(
        "--account",
        action="append",
        default=None,
        metavar="SLUG",
        help=(
            "Multi-account path: run this AutomationAccount slug from accounts.json. "
            "Repeat to include more. Download-only (no Richtato auto-import)."
        ),
    )
    parser.add_argument(
        "--login",
        action="append",
        default=None,
        metavar="LOGIN_ID",
        help=(
            "Multi-account path: run every AutomationAccount under this login from "
            "accounts.json. Repeat to include more. Download-only."
        ),
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Override AUTOMATION_HEADLESS and launch a visible browser (debugging only; requires a display).",
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help=(
            "DB path: pull due BankConnection rows from the Richtato API "
            "instead of reading accounts.json. Used by the polling scheduler."
        ),
    )
    parser.add_argument(
        "--db-all",
        action="store_true",
        help=(
            "DB path: also pick up active connections whose next_run_at is in "
            "the future. Useful for ad-hoc 'run everything' runs."
        ),
    )
    parser.add_argument(
        "--db-connection",
        type=int,
        action="append",
        default=None,
        metavar="ID",
        help=(
            "DB path: limit to specific connection ID(s). Implies --db. Repeat for more."
        ),
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


def _drive_one_account(
    adapter: BofaAccountAdapter,
    context: BrowserContext,
    config: AutomationConfig,
) -> Path:
    """Run the browser flow for one AutomationAccount inside an already-open context."""

    page: Page = context.new_page()
    page.set_default_timeout(adapter.nav_timeout_ms)
    try:
        try:
            page.goto(adapter.url, wait_until="domcontentloaded")
        except PlaywrightTimeoutError as exc:
            raise DomBroken(f"Timed out loading {adapter.url}: {exc}") from exc

        if not adapter.is_session_valid(page):
            raise SessionExpired(f"Session check failed for {adapter.slug}")

        adapter.navigate_to_export(page)
        download = adapter.trigger_download(page)
        return _save_download(download, config.downloads_dir(adapter.slug))
    finally:
        page.close()


def _drive_login(
    login: LoginSession,
    accounts: list[AutomationAccount],
    config: AutomationConfig,
    state: RunState,
    notifier: Notifier,
    headed_override: bool,
) -> int:
    """Run every account under one login inside a single browser context.

    Returns the number of failures so the caller can aggregate run statistics.
    Per-account errors are isolated: a failure on one account does not abort
    the remaining accounts under the same login.
    """

    if not accounts:
        return 0

    storage_state_path = login.storage_state_path
    if not storage_state_path.exists():
        message = (
            f"No storage state file at {storage_state_path}. "
            f"Bootstrap login {login.id!r} with scripts/statement_downloader.py first."
        )
        logger.error("[login={}] {}", login.id, message)
        for account in accounts:
            notifier.record_failure(
                account.slug,
                ErrorKind.SESSION_EXPIRED,
                message,
                state.get(account.slug),
                None,
            )
            state.record_failure(account.slug, message)
        return len(accounts)

    failures = 0
    with _browser_context(config, storage_state_path, headed_override) as context:
        for account in accounts:
            logger.info("[{}] starting (login={})", account.slug, login.id)
            adapter = BofaAccountAdapter(account)
            try:
                downloaded_path = _drive_one_account(adapter, context, config)
            except AutomationError as exc:
                logger.error("[{}] {}: {}", account.slug, exc.kind.value, exc.message)
                notifier.record_failure(
                    account.slug,
                    exc.kind,
                    exc.message,
                    state.get(account.slug),
                    exc,
                )
                state.record_failure(account.slug, exc.message)
                failures += 1
                continue
            except PlaywrightTimeoutError as exc:
                message = f"Playwright timeout: {exc}"
                logger.error("[{}] dom_broken: {}", account.slug, message)
                notifier.record_failure(
                    account.slug,
                    ErrorKind.DOM_BROKEN,
                    message,
                    state.get(account.slug),
                    exc,
                )
                state.record_failure(account.slug, message)
                failures += 1
                continue
            except Exception as exc:
                logger.exception("[{}] unexpected error", account.slug)
                notifier.record_failure(
                    account.slug,
                    ErrorKind.UNKNOWN,
                    str(exc),
                    state.get(account.slug),
                    exc,
                )
                state.record_failure(account.slug, str(exc))
                failures += 1
                continue

            state.record_success(account.slug, downloaded_path)
            logger.info("[{}] success ({})", account.slug, downloaded_path.name)

    return failures


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


def _db_account_to_legacy(db_account: DBAccount, login_id: str) -> AutomationAccount:
    """Bridge ``DBAccount`` -> ``AutomationAccount`` for the existing adapter.

    ``BofaAccountAdapter`` was written before the DB-driven path existed and
    accepts the legacy dataclass. Building an ``AutomationAccount`` here is
    a tiny adapter so we do not have to refactor the adapter signature in
    Phase 1.
    """

    return AutomationAccount(
        slug=db_account.slug,
        login=login_id,
        institution=db_account.institution_slug,
        flow=db_account.flow,
        activity_url=db_account.activity_url,
    )


def _drive_db_connection(
    db_connection: DBConnection,
    config: AutomationConfig,
    headed_override: bool,
) -> tuple[int, int, int, str, str]:
    """Drive every account inside one DB-backed connection.

    Returns ``(attempted, succeeded, statements_imported, failure_kind, failure_reason)``.
    ``failure_kind`` is non-empty only when the whole connection failed at
    the session-validity check; per-account failures are tracked through
    the counters and recorded in the run log.
    """

    raw_accounts = list(db_connection.accounts)
    unbound = [a for a in raw_accounts if a.financial_account_id is None]
    no_url = [
        a
        for a in raw_accounts
        if a.financial_account_id is not None and not a.activity_url
    ]
    accounts = [
        a for a in raw_accounts if a.financial_account_id is not None and a.activity_url
    ]
    if not accounts:
        if unbound and not no_url:
            reason = (
                f"{len(unbound)} captured account(s) waiting for a Richtato account binding "
                "in Bank Sync"
            )
            kind = "needs_binding"
        elif no_url and not unbound:
            reason = (
                f"{len(no_url)} bound account(s) missing an activity URL — recapture "
                "from the account's activity page"
            )
            kind = "needs_activity_url"
        else:
            reason = "No enabled accounts with both a Richtato binding and an activity URL"
            kind = "config"
        logger.warning(
            "[connection={}] {}", db_connection.connection_id, reason
        )
        return 0, 0, 0, kind, reason

    storage_state_path = db_connection.materialize_storage_state()
    attempted = len(accounts)
    succeeded = 0
    statements_imported = 0
    last_failure_kind = ""
    last_failure_reason = ""

    try:
        with _browser_context(config, storage_state_path, headed_override) as context:
            for db_account in accounts:
                legacy = _db_account_to_legacy(db_account, db_connection.login_id)
                try:
                    adapter = get_account_adapter(
                        db_connection.institution_slug, legacy
                    )
                except DomBroken as exc:
                    last_failure_kind = exc.kind.value
                    last_failure_reason = exc.message
                    logger.error(
                        "[connection={}, account={}] {}: {}",
                        db_connection.connection_id,
                        legacy.slug,
                        exc.kind.value,
                        exc.message,
                    )
                    continue
                logger.info(
                    "[connection={}, account={}] starting",
                    db_connection.connection_id,
                    legacy.slug,
                )
                try:
                    downloaded_path = _drive_one_account(adapter, context, config)
                except SessionExpired as exc:
                    logger.warning(
                        "[connection={}] session expired: {}",
                        db_connection.connection_id,
                        exc.message,
                    )
                    return (
                        attempted,
                        succeeded,
                        statements_imported,
                        ErrorKind.SESSION_EXPIRED.value,
                        exc.message,
                    )
                except AutomationError as exc:
                    last_failure_kind = exc.kind.value
                    last_failure_reason = exc.message
                    logger.error(
                        "[connection={}, account={}] {}: {}",
                        db_connection.connection_id,
                        legacy.slug,
                        exc.kind.value,
                        exc.message,
                    )
                    continue
                except PlaywrightTimeoutError as exc:
                    last_failure_kind = ErrorKind.DOM_BROKEN.value
                    last_failure_reason = f"Playwright timeout: {exc}"
                    logger.error(
                        "[connection={}, account={}] dom_broken: {}",
                        db_connection.connection_id,
                        legacy.slug,
                        exc,
                    )
                    continue
                except Exception as exc:
                    last_failure_kind = ErrorKind.UNKNOWN.value
                    last_failure_reason = str(exc)
                    logger.exception(
                        "[connection={}, account={}] unexpected error",
                        db_connection.connection_id,
                        legacy.slug,
                    )
                    continue

                if db_account.financial_account_id is None:
                    logger.warning(
                        "[connection={}, account={}] downloaded but no financial_account_id; skipping import",
                        db_connection.connection_id,
                        legacy.slug,
                    )
                    succeeded += 1
                    continue

                try:
                    submit_statement(
                        config,
                        db_account.institution_slug,
                        downloaded_path,
                        account_id=db_account.financial_account_id,
                    )
                except AutomationError as exc:
                    last_failure_kind = exc.kind.value
                    last_failure_reason = exc.message
                    logger.error(
                        "[connection={}, account={}] import_rejected: {}",
                        db_connection.connection_id,
                        legacy.slug,
                        exc.message,
                    )
                    continue
                except Exception as exc:
                    last_failure_kind = ErrorKind.UNKNOWN.value
                    last_failure_reason = str(exc)
                    logger.exception(
                        "[connection={}, account={}] unexpected import error",
                        db_connection.connection_id,
                        legacy.slug,
                    )
                    continue

                succeeded += 1
                statements_imported += 1
                logger.info(
                    "[connection={}, account={}] success ({})",
                    db_connection.connection_id,
                    legacy.slug,
                    downloaded_path.name,
                )
    finally:
        db_connection.cleanup()

    return (
        attempted,
        succeeded,
        statements_imported,
        last_failure_kind,
        last_failure_reason,
    )


def run_db(
    config: AutomationConfig | None = None,
    *,
    force_all: bool = False,
    connection_ids: list[int] | None = None,
    headed_override: bool = False,
) -> int:
    """Execute a DB-driven pass: fetch due connections and process each.

    Returns the count of connections that ended in a non-success state. The
    backend records detailed run history through the run-outcome endpoint.
    """

    config = config or load_config()
    db_connections = fetch_due_connections(config, force_all=force_all)
    if connection_ids:
        wanted = set(connection_ids)
        db_connections = [c for c in db_connections if c.connection_id in wanted]

    if not db_connections:
        logger.info("DB run: nothing to do (no due connections)")
        return 0

    failures = 0
    for db_connection in db_connections:
        try:
            attempted, succeeded, statements_imported, failure_kind, failure_reason = (
                _drive_db_connection(db_connection, config, headed_override)
            )
        except Exception as exc:
            logger.exception(
                "[connection={}] unhandled exception", db_connection.connection_id
            )
            attempted = len(db_connection.accounts)
            succeeded = 0
            statements_imported = 0
            failure_kind = ErrorKind.UNKNOWN.value
            failure_reason = str(exc)

        connection_succeeded = succeeded > 0 and not failure_kind
        if attempted > 0 and succeeded == attempted and not failure_kind:
            connection_succeeded = True
        if not connection_succeeded:
            failures += 1

        post_run_outcome(
            config,
            run_id=db_connection.run_id,
            succeeded=connection_succeeded,
            failure_kind=failure_kind,
            failure_reason=failure_reason,
            accounts_attempted=attempted,
            accounts_succeeded=succeeded,
            statements_imported=statements_imported,
        )

    logger.info(
        "DB run complete: {} connection(s), {} failure(s)",
        len(db_connections),
        failures,
    )
    return failures


def _resolve_run_list(
    config: AutomationConfig, requested: list[str] | None
) -> list[str]:
    if requested:
        unknown = [slug for slug in requested if slug not in SUPPORTED_INSTITUTIONS]
        if unknown:
            raise SystemExit(f"Unknown institution(s): {', '.join(unknown)}")
        return list(requested)
    return list(config.enabled_institutions)


def _resolve_account_run_list(
    config: AutomationConfig,
    requested_accounts: list[str] | None,
    requested_logins: list[str] | None,
) -> list[AutomationAccount]:
    """Resolve which AutomationAccounts to drive given CLI filters.

    Selection rules:
    - Explicit ``--account`` and ``--login`` filters union to the set of slugs.
    - When neither is provided AND no legacy ``--only`` is in play, all
      accounts from accounts.json run by default.
    - Unknown slugs or login IDs raise SystemExit so misconfigurations fail
      loudly rather than silently skipping.
    """

    if not config.automation_accounts:
        if requested_accounts or requested_logins:
            raise SystemExit(
                "No automation_accounts loaded. Create "
                f"{config.accounts_file} with at least one login and account."
            )
        return []

    known_slugs = {a.slug for a in config.automation_accounts}
    known_logins = set(config.logins)

    if not requested_accounts and not requested_logins:
        return list(config.automation_accounts)

    selected: dict[str, AutomationAccount] = {}

    if requested_accounts:
        unknown = [s for s in requested_accounts if s not in known_slugs]
        if unknown:
            raise SystemExit(f"Unknown account slug(s): {', '.join(unknown)}")
        for slug in requested_accounts:
            account = config.find_account(slug)
            if account is not None:
                selected[account.slug] = account

    if requested_logins:
        unknown = [lid for lid in requested_logins if lid not in known_logins]
        if unknown:
            raise SystemExit(f"Unknown login id(s): {', '.join(unknown)}")
        for login_id in requested_logins:
            for account in config.accounts_for_login(login_id):
                selected[account.slug] = account

    return list(selected.values())


def _group_by_login(
    accounts: list[AutomationAccount],
) -> dict[str, list[AutomationAccount]]:
    grouped: dict[str, list[AutomationAccount]] = {}
    for account in accounts:
        grouped.setdefault(account.login, []).append(account)
    return grouped


def run_all(
    config: AutomationConfig | None = None,
    only: list[str] | None = None,
    accounts: list[str] | None = None,
    logins: list[str] | None = None,
    headed_override: bool = False,
) -> int:
    """Execute one full pass. Returns the number of failures.

    ``only`` drives the legacy institution path (Chase, Marcus, the original
    BoFA adapter) with auto-import. ``accounts`` and ``logins`` drive the new
    multi-account path (BoFA per-account) and are download-only.

    When all filter lists are ``None``:
    - If ``accounts.json`` has entries, run every account there.
    - Otherwise fall back to the legacy enabled-institutions list.
    """

    config = config or load_config()

    institution_filter_explicit = only is not None
    account_filter_explicit = accounts is not None or logins is not None
    has_accounts_config = bool(config.automation_accounts)

    if institution_filter_explicit:
        institutions = _resolve_run_list(config, only)
    else:
        institutions = []

    if account_filter_explicit:
        selected_accounts = _resolve_account_run_list(config, accounts, logins)
    elif institution_filter_explicit:
        selected_accounts = []
    elif has_accounts_config:
        selected_accounts = list(config.automation_accounts)
    else:
        selected_accounts = []

    if (
        not institution_filter_explicit
        and not account_filter_explicit
        and not has_accounts_config
    ):
        institutions = list(config.enabled_institutions)

    if not institutions and not selected_accounts:
        logger.warning(
            "Nothing to do: no institutions and no automation accounts selected."
        )
        return 0

    state = load_state(config.state_file)
    notifier = Notifier(config)

    failures = 0

    grouped = _group_by_login(selected_accounts)
    for login_id, login_accounts in grouped.items():
        login = config.logins.get(login_id)
        if login is None:
            logger.error(
                "[login={}] missing LoginSession; skipping {} account(s)",
                login_id,
                len(login_accounts),
            )
            for account in login_accounts:
                message = f"Unknown login {login_id!r} in accounts.json"
                notifier.record_failure(
                    account.slug,
                    ErrorKind.CONFIG,
                    message,
                    state.get(account.slug),
                    None,
                )
                state.record_failure(account.slug, message)
                failures += 1
            continue
        failures += _drive_login(
            login, login_accounts, config, state, notifier, headed_override
        )

    for slug in institutions:
        if not _run_institution(slug, config, state, notifier, headed_override):
            failures += 1

    _check_stale(config, state, notifier)
    save_state(state, config.state_file)
    notifier.flush()

    total = len(institutions) + len(selected_accounts)
    logger.info(
        "Run complete: {} succeeded, {} failed (institutions={}, accounts={})",
        total - failures,
        failures,
        len(institutions),
        len(selected_accounts),
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

    if args.db or args.db_connection or args.db_all:
        return run_db(
            config,
            force_all=args.db_all or bool(args.db_connection),
            connection_ids=args.db_connection,
            headed_override=args.headed,
        )

    return run_all(
        config,
        only=args.only,
        accounts=args.account,
        logins=args.login,
        headed_override=args.headed,
    )


if __name__ == "__main__":
    raise SystemExit(main())
