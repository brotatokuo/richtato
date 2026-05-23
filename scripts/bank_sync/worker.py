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
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from playwright.async_api import async_playwright

from scripts.bank_sync.agent_store import Account, AgentStore, Login
from scripts.bank_sync.errors import (
    NeedsReauthError,
    NoDownloadError,
)
from scripts.bank_sync.institutions import get_adapter
from scripts.bank_sync.playwright_helpers import capture_storage_state
from scripts.bank_sync.storage import write_statement

HEADED_CHROMIUM_ARGS = [
    "--no-first-run",
    "--no-default-browser-check",
]
HEADED_LAUNCH_TIMEOUT_MS = 60_000


def _x11_available() -> bool:
    """Return ``True`` if the host has a display server (needed for headed sign-in)."""
    return bool(os.environ.get("DISPLAY"))


@dataclass
class DownloadOutcome:
    """Per-login summary returned by :func:`download_login`."""

    attempted: int
    succeeded: int
    files_downloaded: int
    failure_reason: str = ""
    needs_reauth: bool = False


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

    logger.info("Starting interactive login for {} ({})", login.institution_slug, login.nickname or "default")

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
                store.set_login_status(login_id, "error", last_failure_reason=str(exc)[:500])
                return False, f"Adapter crashed: {exc}"

            if page.is_closed():
                store.set_login_status(
                    login_id,
                    "pending_login",
                    last_failure_reason="User closed the browser before sign-in completed.",
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
        payload = discovered.as_payload() if hasattr(discovered, "as_payload") else discovered
        storage_uri = payload.get("storage_uri") or ""
        if not storage_uri:
            # Auto-binding requires the user to know the destination dir; emit
            # a record without storage_uri only if the caller wants to plug it
            # in later via ``account add``.
            continue
        store.add_account(
            login_id=login_id,
            storage_uri=storage_uri,
            activity_url=payload.get("activity_url", ""),
            flow=payload.get("flow", "deposit"),
            detected_account_name=payload.get("detected_account_name", ""),
        )
        new_accounts += 1

    return True, f"Captured cookies; discovered {len(discovered_accounts)} bank-side accounts (added {new_accounts})."


async def download_login(store: AgentStore, login_id: int, *, kind: str = "manual_download") -> DownloadOutcome:
    """Replay stored cookies for ``login_id`` and download every enabled account.

    Each downloaded file is written into the account's ``storage_uri``
    using the canonical ``<year>/<month>/<hash>-<filename>`` layout.
    """
    login = store.get_login(login_id)
    if login is None:
        return DownloadOutcome(attempted=0, succeeded=0, files_downloaded=0, failure_reason="Login not found")

    storage_state_raw = login.storage_state
    if not storage_state_raw:
        store.set_login_status(login_id, "needs_reauth", last_failure_reason="No stored cookies.")
        return DownloadOutcome(
            attempted=0,
            succeeded=0,
            files_downloaded=0,
            failure_reason="No stored cookies; run `bank-agent login signin` first.",
            needs_reauth=True,
        )

    try:
        adapter = get_adapter(login.institution_slug)
    except KeyError as exc:
        return DownloadOutcome(attempted=0, succeeded=0, files_downloaded=0, failure_reason=str(exc))

    accounts = [a for a in store.list_accounts(login_id) if a.enabled and a.activity_url_encrypted]
    if not accounts:
        return DownloadOutcome(attempted=0, succeeded=0, files_downloaded=0, failure_reason="No enabled accounts.")

    storage_state = json.loads(storage_state_raw)
    run = store.start_run(login_id, kind)

    succeeded = 0
    files_downloaded = 0
    failure_reason = ""
    needs_reauth = False

    import tempfile

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                storage_state=storage_state,
                accept_downloads=True,
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()

            for account in accounts:
                with tempfile.TemporaryDirectory() as tmpdir_str:
                    from pathlib import Path as _Path

                    tmpdir = _Path(tmpdir_str)
                    try:
                        file_path = await adapter.download_account(
                            page,
                            activity_url=account.activity_url,
                            flow=account.flow,
                            download_dir=tmpdir,
                        )
                    except NeedsReauthError as exc:
                        needs_reauth = True
                        failure_reason = f"needs_reauth on account {account.id}: {exc}"
                        logger.warning(failure_reason)
                        break
                    except NoDownloadError as exc:
                        logger.warning("no_download on account {}: {}", account.id, exc)
                        continue
                    except Exception as exc:
                        logger.exception("Download crashed for account {}", account.id)
                        failure_reason = failure_reason or f"Account {account.id}: {exc}"
                        continue

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
                        logger.exception("Failed to persist downloaded file for account {}", account.id)
                        failure_reason = failure_reason or f"Account {account.id}: {exc}"
                        continue

                    files_downloaded += 1
                    succeeded += 1
                    store.mark_account_success(account.id)
        finally:
            await browser.close()

    store.finish_run(
        run.id,
        succeeded=(failure_reason == "" and not needs_reauth),
        files_downloaded=files_downloaded,
        error=failure_reason,
    )
    store.record_login_outcome(login_id, succeeded=(failure_reason == "" and not needs_reauth), failure_reason=failure_reason)
    if needs_reauth:
        store.set_login_status(login_id, "needs_reauth", last_failure_reason=failure_reason)

    return DownloadOutcome(
        attempted=len(accounts),
        succeeded=succeeded,
        files_downloaded=files_downloaded,
        failure_reason=failure_reason,
        needs_reauth=needs_reauth,
    )


def _login_summary(login: Login, accounts: list[Account]) -> str:
    return (
        f"#{login.id} [{login.institution_slug}] {login.nickname or '(default)'} "
        f"status={login.status} cadence={login.cadence} accounts={len(accounts)}"
    )
