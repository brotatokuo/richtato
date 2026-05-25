"""Shared Playwright helpers used by the bank-sync adapters."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from loguru import logger
from playwright.async_api import BrowserContext, Download, Page

from scripts.bank_sync.errors import DomBrokenError, NeedsReauthError

# Default upper bound for the user's headed-login flow (sign-in + MFA + 2FA
# prompts). 10 minutes is generous; the agent reports ``login_cancelled``
# if the user gives up before then.
INTERACTIVE_LOGIN_TIMEOUT_MS = 10 * 60 * 1000

# Per-download wait. Banks typically generate CSV/XLS within 5s, but we
# give a 60s ceiling to absorb slow CSV regenerations.
DOWNLOAD_TIMEOUT_MS = 60 * 1000

_REAUTH_TEXT_MARKERS = (
    "sign in",
    "sign-in",
    "log on",
    "log in",
    "session expired",
    "session has expired",
    "verify your identity",
    "multi-factor",
    "two-step verification",
    "enter your password",
    "user id",
    "online id",
)


def is_login_url(url: str, markers: tuple[str, ...]) -> bool:
    """Return ``True`` when ``url`` contains any institution login marker."""
    lowered = (url or "").lower()
    return any(marker in lowered for marker in markers)


def html_body_suggests_reauth(body: bytes) -> bool:
    """Heuristic check for sign-in HTML returned instead of a download."""
    if not body:
        return False
    sample = body[:8000].decode("utf-8", errors="ignore").lower()
    if "<html" not in sample and "<!doctype html" not in sample:
        return False
    return any(marker in sample for marker in _REAUTH_TEXT_MARKERS) or bool(
        re.search(r'\b(type=["\']password["\']|name=["\']password["\'])', sample)
    )


async def page_suggests_reauth(
    page: Page,
    *,
    login_markers: tuple[str, ...],
) -> bool:
    """Return ``True`` when the current page looks like a sign-in screen."""
    try:
        url = page.url or ""
    except Exception:
        return False

    if is_login_url(url, login_markers):
        return True

    try:
        title = (await page.title() or "").lower()
    except Exception:
        title = ""

    if any(marker in title for marker in _REAUTH_TEXT_MARKERS):
        return True

    try:
        body_text = (await page.locator("body").inner_text(timeout=2_000) or "").lower()
    except Exception:
        body_text = ""

    if len(body_text) > 20_000:
        body_text = body_text[:20_000]
    return any(marker in body_text for marker in _REAUTH_TEXT_MARKERS)


async def raise_after_selector_failure(
    page: Page,
    exc: BaseException,
    *,
    login_markers: tuple[str, ...],
    dom_context: str,
) -> None:
    """Classify a selector/timeout failure as reauth or DOM breakage."""
    if await page_suggests_reauth(page, login_markers=login_markers):
        raise NeedsReauthError(f"Session expired during {dom_context}.") from exc
    raise DomBrokenError(f"{dom_context}: {exc}") from exc


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
