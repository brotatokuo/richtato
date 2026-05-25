"""Playwright orchestration for the standalone bank-agent.

This module is intentionally agnostic of the CLI; it operates only on
the local :class:`AgentStore`. Two entry points:

* :func:`interactive_login` — pop a headed Chromium for the user, wait
  for sign-in to land, and persist the captured ``storage_state``.
* :func:`download_login` — replay the stored ``storage_state`` headless
  and download a statement for each enabled account, writing the files
  into the account's ``storage_uri`` directory using the same
  ``<year>/<month>/<hash>-<filename>`` layout the backend scanner
  expects.

Neither function calls Richtato's API. The only contract with the
backend is the storage filesystem.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger
from playwright.async_api import async_playwright

from scripts.bank_sync.agent_store import Account, AgentStore, Login
from scripts.bank_sync.cli_hints import signin_command_hint
from scripts.bank_sync.errors import (
    AgentError,
    FailureKind,
    ImportRejectedError,
    NeedsReauthError,
    format_failure_reason,
    failure_kind_for,
    worst_failure_kind,
)
from scripts.bank_sync.institutions import get_adapter
from scripts.bank_sync.playwright_helpers import capture_storage_state
from scripts.bank_sync.storage import push_balance_snapshot, write_statement

HEADED_CHROMIUM_ARGS = [
    "--no-first-run",
    "--no-default-browser-check",
]
HEADED_LAUNCH_TIMEOUT_MS = 60_000


@dataclass
class AccountFailure:
    """One classified failure for a single account during a sync run."""

    account_id: int
    kind: FailureKind
    message: str


@dataclass
class DownloadOutcome:
    """Per-login summary returned by :func:`download_login`."""

    attempted: int
    succeeded: int
    files_downloaded: int
    failure_reason: str = ""
    needs_reauth: bool = False
    failure_kind: FailureKind | None = None
    account_failures: list[AccountFailure] = field(default_factory=list)
    run_status: str = "completed"


def _x11_available() -> bool:
    """Return ``True`` if the host has a display server (needed for headed sign-in)."""
    return bool(os.environ.get("DISPLAY"))


def _summarize_account_failures(failures: list[AccountFailure]) -> str:
    """Build a concise, prefixed failure summary for vault storage."""
    if not failures:
        return ""
    primary = min(failures, key=lambda item: item.kind)
    if len(failures) == 1:
        return format_failure_reason(
            primary.kind,
            f"Account {primary.account_id}: {primary.message}",
        )
    lines = [f"Account {item.account_id}: {item.message}" for item in failures]
    return format_failure_reason(primary.kind, "; ".join(lines))


def _run_status_for(
    *,
    attempted: int,
    succeeded: int,
    needs_reauth: bool,
    account_failures: list[AccountFailure],
) -> str:
    if needs_reauth or account_failures or succeeded < attempted:
        if succeeded > 0 and not needs_reauth:
            return "partial"
        return "failed"
    return "completed"


def _record_account_failure(
    *,
    login_id: int,
    account_id: int,
    exc: BaseException,
    account_failures: list[AccountFailure],
) -> AccountFailure:
    kind = failure_kind_for(exc)
    message = str(exc)
    failure = AccountFailure(account_id=account_id, kind=kind, message=message)
    account_failures.append(failure)
    logger.warning(
        "account_failure login={} account={} kind={} msg={}",
        login_id,
        account_id,
        kind,
        message,
    )
    return failure


async def interactive_login(store: AgentStore, login_id: int) -> tuple[bool, str]:
    """Open a headed Chromium so the user can sign in to ``login_id``.

    Returns ``(succeeded, message)``. On success, ``storage_state`` is
    captured and persisted, and the login is flipped to ``active``.
    """
    login = store.get_login(login_id)
    if login is None:
        return False, f"Login {login_id} not found"

    if not _x11_available():
        return False, "No DISPLAY found; headed sign-in requires a desktop session."

    try:
        adapter = get_adapter(login.institution_slug)
    except KeyError as exc:
        return False, str(exc)

    logger.info(
        "Starting interactive login for {} ({})",
        login.institution_slug,
        login.nickname or "default",
    )

    discovered_accounts: list[Any] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=HEADED_CHROMIUM_ARGS,
            timeout=HEADED_LAUNCH_TIMEOUT_MS,
        )
        try:
            context = await browser.new_context(
                accept_downloads=True,
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()
            try:
                discovered_accounts = await adapter.interactive_login(context, page)
            except Exception as exc:
                logger.exception("Adapter interactive_login crashed")
                store.set_login_status(
                    login_id,
                    "error",
                    last_failure_reason=format_failure_reason(
                        FailureKind.UNKNOWN, str(exc)[:500]
                    ),
                )
                return False, f"Adapter crashed: {exc}"

            if page.is_closed():
                store.set_login_status(
                    login_id,
                    "pending_login",
                    last_failure_reason=format_failure_reason(
                        FailureKind.LOGIN_CANCELLED,
                        "User closed the browser before sign-in completed.",
                    ),
                )
                return False, "Sign-in cancelled (browser closed)."

            storage_state = await capture_storage_state(context)
        finally:
            await browser.close()

    store.set_storage_state(login_id, json.dumps(storage_state))
    store.update_login_schedule(
        login_id,
        next_run_at=datetime.now(timezone.utc).isoformat(),
    )

    new_accounts = 0
    for discovered in discovered_accounts:
        payload = (
            discovered.as_payload() if hasattr(discovered, "as_payload") else discovered
        )
        storage_uri = payload.get("storage_uri") or ""
        if not storage_uri:
            continue
        store.add_account(
            login_id=login_id,
            storage_uri=storage_uri,
            activity_url=payload.get("activity_url", ""),
            flow=payload.get("flow", "deposit"),
            detected_account_name=payload.get("detected_account_name", ""),
        )
        new_accounts += 1

    return (
        True,
        f"Captured cookies; discovered {len(discovered_accounts)} bank-side accounts (added {new_accounts}).",
    )


async def download_login(
    store: AgentStore,
    login_id: int,
    *,
    kind: str = "manual_download",
    headed: bool = False,
) -> DownloadOutcome:
    """Replay stored cookies for ``login_id`` and download every enabled account.

    Each downloaded file is written into the account's ``storage_uri``
    using the canonical ``<year>/<month>/<hash>-<filename>`` layout.
    """
    login = store.get_login(login_id)
    if login is None:
        return DownloadOutcome(
            attempted=0,
            succeeded=0,
            files_downloaded=0,
            failure_reason=format_failure_reason(FailureKind.CONFIG, "Login not found"),
            failure_kind=FailureKind.CONFIG,
            run_status="failed",
        )
    if headed and not _x11_available():
        return DownloadOutcome(
            attempted=0,
            succeeded=0,
            files_downloaded=0,
            failure_reason=format_failure_reason(
                FailureKind.CONFIG,
                "No DISPLAY found; headed sync requires a desktop session.",
            ),
            failure_kind=FailureKind.CONFIG,
            run_status="failed",
        )

    storage_state_raw = login.storage_state
    if not storage_state_raw:
        reason = format_failure_reason(
            FailureKind.NEEDS_REAUTH,
            f"No stored cookies; run {signin_command_hint(login_id)} first.",
        )
        store.set_login_status(login_id, "needs_reauth", last_failure_reason=reason)
        return DownloadOutcome(
            attempted=0,
            succeeded=0,
            files_downloaded=0,
            failure_reason=reason,
            needs_reauth=True,
            failure_kind=FailureKind.NEEDS_REAUTH,
            run_status="failed",
        )

    try:
        adapter = get_adapter(login.institution_slug)
    except KeyError as exc:
        return DownloadOutcome(
            attempted=0,
            succeeded=0,
            files_downloaded=0,
            failure_reason=format_failure_reason(FailureKind.CONFIG, str(exc)),
            failure_kind=FailureKind.CONFIG,
            run_status="failed",
        )

    accounts = [
        a
        for a in store.list_accounts(login_id)
        if a.enabled
        and a.activity_url_encrypted
        and (a.flow == "investment_balance" or a.storage_uri)
    ]
    if not accounts:
        return DownloadOutcome(
            attempted=0,
            succeeded=0,
            files_downloaded=0,
            failure_reason=format_failure_reason(
                FailureKind.CONFIG, "No enabled accounts."
            ),
            failure_kind=FailureKind.CONFIG,
            run_status="failed",
        )

    storage_state = json.loads(storage_state_raw)
    run = store.start_run(login_id, kind)

    succeeded = 0
    files_downloaded = 0
    needs_reauth = False
    account_failures: list[AccountFailure] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=not headed,
            args=HEADED_CHROMIUM_ARGS if headed else None,
            timeout=HEADED_LAUNCH_TIMEOUT_MS if headed else None,
        )
        try:
            context = await browser.new_context(
                storage_state=storage_state,
                accept_downloads=True,
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()

            for account in accounts:
                if account.flow == "investment_balance":
                    stop = await _sync_investment_account(
                        store=store,
                        login_id=login_id,
                        adapter=adapter,
                        page=page,
                        account=account,
                        account_failures=account_failures,
                    )
                    if stop:
                        needs_reauth = True
                        break
                    if not any(
                        failure.account_id == account.id for failure in account_failures
                    ):
                        succeeded += 1
                    continue

                stop = await _sync_statement_account(
                    store=store,
                    login_id=login_id,
                    adapter=adapter,
                    page=page,
                    account=account,
                    account_failures=account_failures,
                )
                if stop[0]:
                    needs_reauth = True
                    break
                if stop[1]:
                    files_downloaded += 1
                if not any(
                    failure.account_id == account.id for failure in account_failures
                ):
                    succeeded += 1
        finally:
            await browser.close()

    failure_reason = _summarize_account_failures(account_failures)
    if needs_reauth and not failure_reason:
        failure_reason = format_failure_reason(
            FailureKind.NEEDS_REAUTH, "Session expired during sync."
        )

    failure_kind = (
        FailureKind.NEEDS_REAUTH
        if needs_reauth
        else worst_failure_kind([item.kind for item in account_failures])
    )
    run_status = _run_status_for(
        attempted=len(accounts),
        succeeded=succeeded,
        needs_reauth=needs_reauth,
        account_failures=account_failures,
    )
    run_succeeded_fully = run_status == "completed"

    store.finish_run(
        run.id,
        status=run_status,
        files_downloaded=files_downloaded,
        error=failure_reason,
    )
    store.record_login_outcome(
        login_id,
        succeeded=run_succeeded_fully,
        failure_reason=failure_reason,
    )
    if needs_reauth:
        store.set_login_status(
            login_id, "needs_reauth", last_failure_reason=failure_reason
        )

    logger.info(
        "run_finished login={} run={} status={} kind={} attempted={} succeeded={} files={}",
        login_id,
        run.id,
        run_status,
        failure_kind or "none",
        len(accounts),
        succeeded,
        files_downloaded,
    )

    return DownloadOutcome(
        attempted=len(accounts),
        succeeded=succeeded,
        files_downloaded=files_downloaded,
        failure_reason=failure_reason,
        needs_reauth=needs_reauth,
        failure_kind=failure_kind,
        account_failures=account_failures,
        run_status=run_status,
    )


async def _sync_investment_account(
    *,
    store: AgentStore,
    login_id: int,
    adapter: Any,
    page: Any,
    account: Account,
    account_failures: list[AccountFailure],
) -> bool:
    """Fetch and push one investment balance. Returns ``True`` to stop the run."""
    try:
        balance = await adapter.fetch_account_balance(
            page,
            activity_url=account.activity_url,
        )
    except NeedsReauthError as exc:
        _record_account_failure(
            login_id=login_id,
            account_id=account.id,
            exc=exc,
            account_failures=account_failures,
        )
        return True
    except AgentError as exc:
        _record_account_failure(
            login_id=login_id,
            account_id=account.id,
            exc=exc,
            account_failures=account_failures,
        )
        return False
    except Exception as exc:
        logger.exception("Balance fetch crashed for account {}", account.id)
        _record_account_failure(
            login_id=login_id,
            account_id=account.id,
            exc=exc,
            account_failures=account_failures,
        )
        return False

    if not account.richtato_account_id:
        _record_account_failure(
            login_id=login_id,
            account_id=account.id,
            exc=ImportRejectedError(
                "Missing richtato_account_id for balance push."
            ),
            account_failures=account_failures,
        )
        return False

    try:
        now = datetime.now(timezone.utc).astimezone()
        push_balance_snapshot(
            richtato_account_id=account.richtato_account_id,
            balance=balance,
            balance_date=now.date(),
        )
        logger.info(
            "Pushed balance account={} richtato_id={} balance={}",
            account.id,
            account.richtato_account_id,
            balance,
        )
    except Exception as exc:
        logger.exception("Failed to push balance for account {}", account.id)
        _record_account_failure(
            login_id=login_id,
            account_id=account.id,
            exc=ImportRejectedError(str(exc)),
            account_failures=account_failures,
        )
        return False

    store.mark_account_success(account.id)
    return False


async def _sync_statement_account(
    *,
    store: AgentStore,
    login_id: int,
    adapter: Any,
    page: Any,
    account: Account,
    account_failures: list[AccountFailure],
) -> tuple[bool, bool]:
    """Download and persist one statement.

    Returns ``(stop_run, file_written)``.
    """
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        try:
            file_path = await adapter.download_account(
                page,
                activity_url=account.activity_url,
                flow=account.flow,
                download_dir=tmpdir,
            )
        except NeedsReauthError as exc:
            _record_account_failure(
                login_id=login_id,
                account_id=account.id,
                exc=exc,
                account_failures=account_failures,
            )
            return True, False
        except AgentError as exc:
            _record_account_failure(
                login_id=login_id,
                account_id=account.id,
                exc=exc,
                account_failures=account_failures,
            )
            return False, False
        except Exception as exc:
            logger.exception("Download crashed for account {}", account.id)
            _record_account_failure(
                login_id=login_id,
                account_id=account.id,
                exc=exc,
                account_failures=account_failures,
            )
            return False, False

        try:
            content = file_path.read_bytes()
            now = datetime.now(timezone.utc).astimezone()
            written = write_statement(
                account.storage_uri,
                year=now.year,
                month=now.month,
                filename=file_path.name,
                content=content,
            )
            logger.info(
                "Wrote statement account={} path={} hash={}",
                account.id,
                written.absolute_path,
                written.sha256[:12],
            )
        except Exception as exc:
            logger.exception(
                "Failed to persist downloaded file for account {}",
                account.id,
            )
            _record_account_failure(
                login_id=login_id,
                account_id=account.id,
                exc=ImportRejectedError(str(exc)),
                account_failures=account_failures,
            )
            return False, False

        store.mark_account_success(account.id)
        return False, True


def _login_summary(login: Login, accounts: list[Account]) -> str:
    return (
        f"#{login.id} [{login.institution_slug}] {login.nickname or '(default)'} "
        f"status={login.status} cadence={login.cadence} accounts={len(accounts)}"
    )
