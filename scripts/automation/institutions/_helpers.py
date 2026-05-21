"""Shared helpers used by multiple institution adapters."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from playwright.sync_api import (
    Download,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from scripts.automation.errors import DomBroken, NoDownload, SessionExpired


def assert_not_on_login(page: Page, login_url_fragments: Iterable[str]) -> None:
    """Raise :class:`SessionExpired` if the page URL contains any login fragment."""

    current_url = page.url.lower()
    for fragment in login_url_fragments:
        if fragment.lower() in current_url:
            raise SessionExpired(f"Redirected to login page: {page.url}")


def first_visible(
    page: Page, selectors: Iterable[str], timeout_ms: int = 5_000
) -> Locator | None:
    """Return the first visible locator matching any selector, or None if none appear in time."""

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout_ms)
            return locator
        except PlaywrightTimeoutError:
            continue
    return None


def expect_download(
    page: Page, action: Callable[[], None], timeout_ms: int
) -> Download:
    """Wrap ``action`` in ``page.expect_download`` and convert timeouts to :class:`NoDownload`."""

    try:
        with page.expect_download(timeout=timeout_ms) as download_info:
            action()
        return download_info.value
    except PlaywrightTimeoutError as exc:
        raise NoDownload("No download event fired within the timeout") from exc


def click_or_break(locator: Locator | None, description: str) -> None:
    """Click ``locator`` or raise :class:`DomBroken` with a helpful description."""

    if locator is None:
        raise DomBroken(f"Could not find {description}")
    try:
        locator.click()
    except PlaywrightTimeoutError as exc:
        raise DomBroken(f"Failed to click {description}: {exc}") from exc


def require(locator: Locator | None, description: str) -> Locator:
    """Return ``locator`` or raise :class:`DomBroken` if it's missing."""

    if locator is None:
        raise DomBroken(f"Could not find {description}")
    return locator
