"""Bank-sync Playwright agent: single poll loop, two task kinds.

The agent runs forever inside the ``automation`` Docker container, polling
``/api/v1/bank-sync/runner/due-tasks/`` every ``BANK_SYNC_POLL_SECONDS``
seconds. Each leased task is dispatched on ``task_kind``:

* ``interactive_login`` — spawn a headed Chromium window so the user can
  sign in to their bank. The cookie ``storage_state`` is captured along
  with a list of discovered accounts and posted back.
* ``scheduled_download`` / ``manual_download`` — replay the stored
  ``storage_state`` headless, navigate each per-account ``activity_url``,
  and download a statement. Downloaded files are POSTed to
  ``/api/v1/accounts/import-statement/``.

Bank passwords never touch this process.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
from pathlib import Path
from typing import Any

from loguru import logger
from playwright.async_api import async_playwright

from scripts.bank_sync.api_client import APIClient, AgentConfig
from scripts.bank_sync.errors import (
    LoginCancelledError,
    NeedsReauthError,
    NoDownloadError,
)
from scripts.bank_sync.institutions import get_adapter
from scripts.bank_sync.institutions.base import BaseInstitutionAdapter
from scripts.bank_sync.playwright_helpers import capture_storage_state


def _configure_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level=os.getenv("BANK_SYNC_LOG_LEVEL", "INFO"))


_X11_HINT = (
    "Headed Chromium needs an X server. On Docker Desktop, run the TCP "
    "bridge on the host, then restart automation with the X11 overlay:\n"
    "  xhost +local:\n"
    "  cp \"$XAUTHORITY\" local_data/.xauthority\n"
    "  python3 scripts/bank_sync/x11_bridge.py\n"
    "  docker compose -f docker-compose.yml -f docker-compose.x11.yml up -d automation"
)


def _x11_available() -> bool:
    """Return True if the container looks ready to launch a headed browser."""

    display = os.environ.get("DISPLAY", "")
    if not display:
        return False
    # TCP mode (Docker Desktop): host.docker.internal:N with a mounted cookie.
    if "host.docker.internal" in display or not display.startswith(":"):
        return Path(os.environ.get("XAUTHORITY", "/tmp/.xauthority")).exists()
    # Unix-socket mode (native Linux Docker): /tmp/.X11-unix must be mounted.
    return Path("/tmp/.X11-unix").exists()


async def _run_interactive_login(
    api: APIClient,
    adapter: BaseInstitutionAdapter,
    task: dict[str, Any],
) -> None:
    """Pop a headed browser, capture storage_state, report back."""

    run_id = task["run_id"]
    user_id = task["user_id"]
    bank_login_id = task["bank_login_id"]

    logger.info(
        "[run={}] Interactive login: institution={} user_id={} login_id={}",
        run_id,
        adapter.slug,
        user_id,
        bank_login_id,
    )

    if not _x11_available():
        logger.warning("[run={}] X11 not available; failing interactive_login", run_id)
        api.post_run_outcome(
            run_id,
            succeeded=False,
            failure_kind="config",
            failure_reason=_X11_HINT,
        )
        return

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        try:
            context = await browser.new_context(
                accept_downloads=True,
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()
            try:
                discovered = await adapter.interactive_login(context, page)
            except Exception as exc:
                logger.exception("Adapter interactive_login crashed")
                api.post_run_outcome(
                    run_id,
                    succeeded=False,
                    failure_kind="dom_broken",
                    failure_reason=str(exc)[:500],
                )
                return

            if page.is_closed():
                # User closed the window without finishing sign-in.
                api.post_run_outcome(
                    run_id,
                    succeeded=False,
                    failure_kind="login_cancelled",
                    failure_reason="User closed the browser before sign-in completed.",
                )
                return

            storage_state = await capture_storage_state(context)
        finally:
            await browser.close()

    try:
        api.post_captured_session(
            run_id,
            storage_state=storage_state,
            discovered_accounts=[d.as_payload() for d in discovered],
        )
    except Exception as exc:
        logger.exception("captured-session POST failed")
        api.post_run_outcome(
            run_id,
            succeeded=False,
            failure_kind="config",
            failure_reason=f"captured-session POST failed: {exc}",
        )
        return

    api.post_run_outcome(
        run_id,
        succeeded=True,
        accounts_attempted=len(discovered),
        accounts_succeeded=len(discovered),
        statements_imported=0,
    )
    logger.info("[run={}] Interactive login complete: discovered={}", run_id, len(discovered))


async def _run_download(
    api: APIClient,
    adapter: BaseInstitutionAdapter,
    task: dict[str, Any],
    *,
    download_root: Path,
) -> None:
    """Headlessly download each enabled account's statement, then post outcomes."""

    run_id = task["run_id"]
    accounts = task.get("accounts") or []
    storage_state_raw = task.get("storage_state") or ""
    if not storage_state_raw:
        api.post_run_outcome(
            run_id,
            succeeded=False,
            failure_kind="needs_reauth",
            failure_reason="No stored session; user must sign in again.",
        )
        return
    storage_state = json.loads(storage_state_raw) if isinstance(storage_state_raw, str) else storage_state_raw

    eligible = [a for a in accounts if a.get("activity_url") and a.get("financial_account_id")]
    if not eligible:
        api.post_run_outcome(
            run_id,
            succeeded=True,
            accounts_attempted=0,
            accounts_succeeded=0,
            statements_imported=0,
        )
        logger.info("[run={}] No bound accounts with activity_url; nothing to download", run_id)
        return

    institution_name = task.get("institution_name", "")
    download_dir = download_root / str(task["user_id"]) / str(task["bank_login_id"]) / str(run_id)
    download_dir.mkdir(parents=True, exist_ok=True)

    succeeded = 0
    imported = 0
    failure_kind = ""
    failure_reason = ""

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                storage_state=storage_state,
                accept_downloads=True,
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()
            for account in eligible:
                try:
                    file_path = await adapter.download_account(
                        page,
                        activity_url=account["activity_url"],
                        flow=account.get("flow", "deposit"),
                        download_dir=download_dir,
                    )
                except NeedsReauthError as exc:
                    failure_kind = "needs_reauth"
                    failure_reason = str(exc)
                    logger.warning(
                        "[run={}] needs_reauth on account {}: {}",
                        run_id,
                        account.get("financial_account_id"),
                        exc,
                    )
                    break
                except NoDownloadError as exc:
                    logger.warning(
                        "[run={}] no_download on account {}: {}",
                        run_id,
                        account.get("financial_account_id"),
                        exc,
                    )
                    continue
                except Exception as exc:
                    logger.exception("[run={}] Unexpected error downloading account", run_id)
                    failure_kind = failure_kind or "dom_broken"
                    failure_reason = failure_reason or str(exc)
                    continue

                try:
                    api.import_statement(
                        account_id=account["financial_account_id"],
                        institution=institution_name,
                        file_path=str(file_path),
                    )
                    imported += 1
                except Exception as exc:
                    logger.exception("[run={}] import-statement failed", run_id)
                    failure_kind = failure_kind or "import_rejected"
                    failure_reason = failure_reason or str(exc)
                    continue

                succeeded += 1
        finally:
            await browser.close()

    api.post_run_outcome(
        run_id,
        succeeded=failure_kind == "",
        failure_kind=failure_kind,
        failure_reason=failure_reason[:500],
        accounts_attempted=len(eligible),
        accounts_succeeded=succeeded,
        statements_imported=imported,
    )
    logger.info(
        "[run={}] Download complete: attempted={} succeeded={} imported={} kind={}",
        run_id,
        len(eligible),
        succeeded,
        imported,
        failure_kind or "ok",
    )


async def _dispatch(api: APIClient, task: dict[str, Any], *, download_root: Path) -> None:
    """Route one leased task to the correct handler based on ``task_kind``."""

    slug = task.get("institution_slug", "")
    try:
        adapter = get_adapter(slug)
    except KeyError:
        api.post_run_outcome(
            task["run_id"],
            succeeded=False,
            failure_kind="config",
            failure_reason=f"No adapter installed for institution {slug!r}.",
        )
        return

    kind = task.get("task_kind", "")
    if kind == "interactive_login":
        await _run_interactive_login(api, adapter, task)
    elif kind in ("scheduled_download", "manual_download"):
        await _run_download(api, adapter, task, download_root=download_root)
    else:
        api.post_run_outcome(
            task["run_id"],
            succeeded=False,
            failure_kind="config",
            failure_reason=f"Unknown task_kind {kind!r}",
        )


async def _poll_loop(api: APIClient) -> None:
    """Forever-loop that leases and runs due tasks."""

    download_root = Path(api.cfg.storage_root)
    download_root.mkdir(parents=True, exist_ok=True)

    stop = asyncio.Event()

    def _shutdown(*_: Any) -> None:
        logger.info("Shutdown signal received; stopping after current task")
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _shutdown)
        except ValueError:  # pragma: no cover - non-main thread
            pass

    logger.info("Bank-sync agent online; polling every {}s", api.cfg.poll_seconds)
    while not stop.is_set():
        try:
            tasks = api.fetch_due_tasks()
        except Exception:
            logger.exception("Failed to fetch due tasks; sleeping before retry")
            tasks = []

        for task in tasks:
            if stop.is_set():
                break
            try:
                await _dispatch(api, task, download_root=download_root)
            except Exception as exc:
                logger.exception("Unhandled task error; reporting failure")
                try:
                    api.post_run_outcome(
                        task["run_id"],
                        succeeded=False,
                        failure_kind="unknown",
                        failure_reason=str(exc)[:500],
                    )
                except Exception:
                    logger.exception("Failed to post failure outcome")

        if stop.is_set():
            break
        try:
            await asyncio.wait_for(asyncio.sleep(api.cfg.poll_seconds), timeout=api.cfg.poll_seconds + 1)
        except Exception:
            pass


def main() -> None:
    _configure_logging()
    cfg = AgentConfig.from_env()
    api = APIClient(cfg)
    try:
        asyncio.run(_poll_loop(api))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
