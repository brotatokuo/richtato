"""Robinhood brokerage adapter (cookie-only, portfolio balance scrape)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from loguru import logger
from playwright.async_api import BrowserContext, Page

from scripts.bank_sync.errors import NeedsReauthError, NoDownloadError
from scripts.bank_sync.institutions.base import (
    BaseInstitutionAdapter,
    DiscoveredAccount,
)
from scripts.bank_sync.playwright_helpers import (
    is_login_url,
    raise_after_selector_failure,
    wait_for_user_login,
)

_LOGIN = "https://robinhood.com/login"
_PORTFOLIO_URL = "https://robinhood.com/?classic=1"
_LOGGED_IN_URLS = ("classic=1",)
_LOGIN_URL_MARKERS = ("/login", "/signup", "/sign-up")
_PORTFOLIO_VALUE_SELECTOR = '[data-testid="PortfolioValue"]'
_ACCOUNT_COMBOBOX_SELECTOR = 'button[role="combobox"]'
_BALANCE_AMOUNT_RE = re.compile(r"-?\$?\s*([\d,]+\.\d{2})")
_BALANCE_WAIT_MS = 30_000
_ACCOUNT_QUERY_KEY = "rh_account"


def parse_balance_text(text: str) -> Decimal:
    """Parse a currency string such as ``$165,706.11`` into a Decimal."""
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


def portfolio_url_for_account(account_name: str) -> str:
    """Build a stable activity URL that encodes the Robinhood account label."""
    label = (account_name or "").strip()
    if not label:
        return _PORTFOLIO_URL
    parsed = urlparse(_PORTFOLIO_URL)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query[_ACCOUNT_QUERY_KEY] = [label]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def account_name_from_activity_url(activity_url: str) -> str:
    """Extract the Robinhood account label from an encoded activity URL."""
    parsed = urlparse(activity_url or "")
    values = parse_qs(parsed.query).get(_ACCOUNT_QUERY_KEY, [])
    return values[0].strip() if values else ""


class RobinhoodAdapter(BaseInstitutionAdapter):
    slug = "robinhood"
    institution_display_name = "Robinhood"
    login_url = _LOGIN
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
        await page.goto(_PORTFOLIO_URL, wait_until="domcontentloaded")
        if not logged_in:
            url = (page.url or "").lower()
            if any(marker in url for marker in _LOGIN_URL_MARKERS):
                return []
        return await self._discover_accounts(page)

    async def _discover_accounts(self, page: Page) -> list[DiscoveredAccount]:
        accounts: list[DiscoveredAccount] = []
        seen: set[str] = set()

        try:
            combobox = page.locator(_ACCOUNT_COMBOBOX_SELECTOR).first
            await combobox.wait_for(state="visible", timeout=_BALANCE_WAIT_MS)
        except Exception:
            logger.info(
                "Robinhood account combobox not found; using default portfolio account"
            )
            return [
                DiscoveredAccount(
                    detected_account_name="Robinhood Brokerage",
                    activity_url=_PORTFOLIO_URL,
                    flow="investment_balance",
                )
            ]

        await combobox.click()
        options = page.get_by_role("option")
        option_count = await options.count()
        if option_count == 0:
            label = (await combobox.inner_text() or "").strip() or "Robinhood Brokerage"
            accounts.append(
                DiscoveredAccount(
                    detected_account_name=label[:255],
                    activity_url=portfolio_url_for_account(label),
                    flow="investment_balance",
                )
            )
        else:
            for index in range(option_count):
                option = options.nth(index)
                label = (await option.inner_text() or "").strip()
                if not label or label in seen:
                    continue
                seen.add(label)
                accounts.append(
                    DiscoveredAccount(
                        detected_account_name=label[:255],
                        activity_url=portfolio_url_for_account(label),
                        flow="investment_balance",
                    )
                )
            await page.keyboard.press("Escape")

        logger.info("Robinhood discovery surfaced {} account(s)", len(accounts))
        return accounts

    async def fetch_account_balance(
        self,
        page: Page,
        *,
        activity_url: str,
    ) -> Decimal:
        target_url = activity_url or _PORTFOLIO_URL
        account_name = account_name_from_activity_url(target_url)
        await page.goto(target_url, wait_until="domcontentloaded")
        self._raise_if_needs_reauth(page)

        if account_name:
            await self._select_account(page, account_name)

        try:
            portfolio_value = page.locator(_PORTFOLIO_VALUE_SELECTOR).first
            await portfolio_value.wait_for(state="visible", timeout=_BALANCE_WAIT_MS)
        except Exception as exc:
            self._raise_if_needs_reauth(page)
            await raise_after_selector_failure(
                page,
                exc,
                login_markers=_LOGIN_URL_MARKERS,
                dom_context=f"Robinhood portfolio value not found at {target_url}",
            )

        aria_label = (await portfolio_value.get_attribute("aria-label") or "").strip()
        if aria_label:
            balance = parse_balance_text(aria_label)
        else:
            text = (await portfolio_value.inner_text() or "").strip()
            balance = parse_balance_text(text)

        logger.info(
            "Robinhood balance scraped from {} (account={!r}): {}",
            target_url,
            account_name or "default",
            balance,
        )
        return balance

    async def _select_account(self, page: Page, account_name: str) -> None:
        combobox = page.locator(_ACCOUNT_COMBOBOX_SELECTOR).first
        await combobox.wait_for(state="visible", timeout=_BALANCE_WAIT_MS)
        current_label = (await combobox.inner_text() or "").strip()
        if current_label == account_name:
            return

        await combobox.click()
        option = page.get_by_role("option", name=account_name, exact=True)
        await option.wait_for(state="visible", timeout=_BALANCE_WAIT_MS)
        await option.click()

    async def download_account(
        self,
        page: Page,
        *,
        activity_url: str,
        flow: str,
        download_dir: Path,
    ) -> Path:
        raise NoDownloadError(
            "Robinhood investment balances use balance scrape; statement downloads are not implemented."
        )

    def _raise_if_needs_reauth(self, page: Page) -> None:
        url = (page.url or "").lower()
        if is_login_url(url, _LOGIN_URL_MARKERS):
            raise NeedsReauthError("Robinhood session expired; sign in again.")
