"""Shared Playwright helpers used by the bank-sync adapters."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from playwright.async_api import BrowserContext, Download, Page

# Default upper bound for the user's headed-login flow (sign-in + MFA + 2FA
# prompts). 10 minutes is generous; the agent reports ``login_cancelled``
# if the user gives up before then.
INTERACTIVE_LOGIN_TIMEOUT_MS = 10 * 60 * 1000

# Per-download wait. Banks typically generate CSV/XLS within 5s, but we
# give a 60s ceiling to absorb slow CSV regenerations.
DOWNLOAD_TIMEOUT_MS = 60 * 1000


async def wait_for_user_login(
    page: Page,
    *,
    success_url_substrings: tuple[str, ...],
    timeout_ms: int = INTERACTIVE_LOGIN_TIMEOUT_MS,
) -> bool:
    """Block until the page URL contains one of ``success_url_substrings``.

    Returns ``True`` on success, ``False`` if the page or browser is closed
    before the URL matches. Used by every adapter's ``interactive_login``
    step instead of selectors so we don't have to write per-bank "logged in"
    detectors.
    """

    end_at_ms = asyncio.get_event_loop().time() * 1000 + timeout_ms
    while True:
        try:
            url = page.url or ""
        except Exception:  # page or context closed
            return False
        if any(s in url for s in success_url_substrings):
            return True
        try:
            await asyncio.wait_for(asyncio.sleep(1), timeout=1.5)
        except Exception:
            pass
        if page.is_closed():
            return False
        if asyncio.get_event_loop().time() * 1000 > end_at_ms:
            logger.warning("Login timed out after {}ms; URL={}", timeout_ms, page.url)
            return False


async def capture_storage_state(context: BrowserContext) -> dict[str, Any]:
    """Serialize the browser cookies + localStorage into a Playwright storage_state dict."""

    return await context.storage_state()


async def download_to_dir(
    page: Page,
    *,
    download_dir: Path,
    trigger,
    timeout_ms: int = DOWNLOAD_TIMEOUT_MS,
) -> Path:
    """Run ``trigger`` and save the resulting download to ``download_dir``.

    Returns the saved path. Raises ``TimeoutError`` if no download appears.
    """

    download_dir.mkdir(parents=True, exist_ok=True)
    async with page.expect_download(timeout=timeout_ms) as info:
        await trigger()
    download: Download = await info.value
    suggested = download.suggested_filename or "statement.csv"
    target = download_dir / suggested
    await download.save_as(str(target))
    logger.info("Downloaded {}", target)
    return target
