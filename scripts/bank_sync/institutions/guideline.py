"""Guideline 401(k) adapter (cookie-only, balance scrape)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urljoin

from loguru import logger
from playwright.async_api import BrowserContext, Page

from scripts.bank_sync.errors import NeedsReauthError, NoDownloadError
from scripts.bank_sync.institutions.base import BaseInstitutionAdapter, DiscoveredAccount
from scripts.bank_sync.playwright_helpers import (
    is_login_url,
    raise_after_selector_failure,
    wait_for_user_login,
)

_HOME = "https://my.guideline.com/"
_LOGGED_IN_URLS = ("/savers/", "/dashboard")
_LOGIN_URL_MARKERS = ("/login", "/sign-in", "/signin", "/auth")
_BALANCE_SELECTOR = '[data-test-id="balance-breakdown"] h2'
_401K_PATH_RE = re.compile(r"/savers/401k/([^/?#]+)")
_BALANCE_AMOUNT_RE = re.compile(r"-?\$?\s*([\d,]+\.\d{2})")
_BALANCE_WAIT_MS = 30_000


def parse_balance_text(text: str) -> Decimal:
    """Parse a currency string such as ``$46,842.67`` into a Decimal."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise NoDownloadError("Balance text was empty.")
    match = _BALANCE_AMOUNT_RE.search(cleaned)
    if not match:
        raise NoDownloadError(f"Could not parse balance from text: {cleaned!r}")
    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation as exc:
        raise NoDownloadError(f"Invalid balance amount: {cleaned!r}") from exc


class GuidelineAdapter(BaseInstitutionAdapter):
    slug = "guideline"
    institution_display_name = "Guideline"
    login_url = _HOME
    post_login_url_substrings = _LOGGED_IN_URLS

    async def interactive_login(
        self,
        context: BrowserContext,
        page: Page,
    ) -> list[DiscoveredAccount]:
        await page.goto(self.login_url, wait_until="domcontentloaded")
        logged_in = await wait_for_user_login(
            page, success_url_substrings=self.post_login_url_substrings
        )
        if not logged_in:
            return []
        return await self._discover_accounts(page)

    async def _discover_accounts(self, page: Page) -> list[DiscoveredAccount]:
        accounts: list[DiscoveredAccount] = []
        seen: set[str] = set()

        anchors = await page.query_selector_all("a[href*='/savers/401k/']")
        for anchor in anchors:
            href = (await anchor.get_attribute("href") or "").strip()
            if not href:
                continue
            absolute = urljoin(page.url, href)
            match = _401K_PATH_RE.search(absolute)
            if not match or match.group(1) in seen:
                continue
            seen.add(match.group(1))
            name = (await anchor.inner_text() or "").strip() or "Guideline 401(k)"
            accounts.append(
                DiscoveredAccount(
                    detected_account_name=name[:255],
                    activity_url=absolute,
                    external_account_token=match.group(1),
                    flow="investment_balance",
                )
            )

        logger.info("Guideline discovery surfaced {} account(s)", len(accounts))
        return accounts

    async def fetch_account_balance(
        self,
        page: Page,
        *,
        activity_url: str,
    ) -> Decimal:
        await page.goto(activity_url, wait_until="domcontentloaded")
        self._raise_if_needs_reauth(page)

        try:
            heading = page.locator(_BALANCE_SELECTOR).first
            await heading.wait_for(state="visible", timeout=_BALANCE_WAIT_MS)
        except Exception as exc:
            self._raise_if_needs_reauth(page)
            await raise_after_selector_failure(
                page,
                exc,
                login_markers=_LOGIN_URL_MARKERS,
                dom_context=f"Guideline balance element not found at {activity_url}",
            )

        text = (await heading.inner_text() or "").strip()
        balance = parse_balance_text(text)
        logger.info("Guideline balance scraped from {}: {}", activity_url, balance)
        return balance

    async def download_account(
        self,
        page: Page,
        *,
        activity_url: str,
        flow: str,
        download_dir: Path,
    ) -> Path:
        raise NoDownloadError("Guideline does not support statement downloads via Playwright.")

    def _raise_if_needs_reauth(self, page: Page) -> None:
        url = (page.url or "").lower()
        if is_login_url(url, _LOGIN_URL_MARKERS):
            raise NeedsReauthError("Guideline session expired; sign in again.")
