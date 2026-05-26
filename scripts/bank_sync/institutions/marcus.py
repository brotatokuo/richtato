"""Marcus by Goldman Sachs adapter (cookie-only, aggregated balance scrape)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from loguru import logger
from playwright.async_api import BrowserContext, Page

from scripts.bank_sync.errors import NeedsReauthError, NoDownloadError
from scripts.bank_sync.institutions.base import BaseInstitutionAdapter, DiscoveredAccount
from scripts.bank_sync.institutions.guideline import parse_balance_text
from scripts.bank_sync.playwright_helpers import (
    is_login_url,
    raise_after_selector_failure,
    wait_for_user_login,
)

_LOGIN = "https://www.marcus.com/us/en/login"
_LOGGED_IN_URLS = ("/dashboard", "/accounts", "marcus.com/us/en")
_LOGIN_URL_MARKERS = ("/login", "/sign-in", "/signin", "/auth")
_ACCOUNT_LIST_SELECTOR = "#marcus-accounts-lists-wrapper, [data-testid='AccountLists']"
_ACCOUNT_ROW_SELECTOR = "div.InteractiveTableRowListItem[id^='row-']"
_ROW_BALANCE_SELECTOR = "div.FlexBox:has(p:text-is('Current balance')) span.NumberDisplay"
_BALANCE_WAIT_MS = 30_000


def sum_row_balances(balances: list[Decimal]) -> Decimal:
    """Return the total of per-account row balances."""
    if not balances:
        raise NoDownloadError("No Marcus account balances found to sum.")
    return sum(balances, Decimal(0))


class MarcusAdapter(BaseInstitutionAdapter):
    slug = "marcus"
    institution_display_name = "Marcus"
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
        if not logged_in:
            return []
        return await self._discover_accounts(page)

    async def _discover_accounts(self, page: Page) -> list[DiscoveredAccount]:
        activity_url = await self._resolve_activity_url(page)
        logger.info("Marcus discovery surfaced 1 aggregated account at {}", activity_url)
        return [
            DiscoveredAccount(
                detected_account_name="Marcus (all accounts)",
                activity_url=activity_url,
                flow="investment_balance",
            )
        ]

    async def fetch_account_balance(
        self,
        page: Page,
        *,
        activity_url: str,
    ) -> Decimal:
        target_url = activity_url or page.url
        if target_url:
            await page.goto(target_url, wait_until="domcontentloaded")
        self._raise_if_needs_reauth(page)

        try:
            account_list = page.locator(_ACCOUNT_LIST_SELECTOR).first
            await account_list.wait_for(state="visible", timeout=_BALANCE_WAIT_MS)
        except Exception as exc:
            self._raise_if_needs_reauth(page)
            await raise_after_selector_failure(
                page,
                exc,
                login_markers=_LOGIN_URL_MARKERS,
                dom_context=f"Marcus account list not found at {target_url or page.url}",
            )

        balances = await self._scrape_row_balances(page)
        total = sum_row_balances(balances)
        logger.info(
            "Marcus balance scraped from {} ({} row(s)): {}",
            target_url or page.url,
            len(balances),
            total,
        )
        return total

    async def _scrape_row_balances(self, page: Page) -> list[Decimal]:
        rows = page.locator(_ACCOUNT_ROW_SELECTOR)
        row_count = await rows.count()
        if row_count == 0:
            raise NoDownloadError("Marcus account list has no account rows.")

        balances: list[Decimal] = []
        for index in range(row_count):
            row = rows.nth(index)
            balance_el = row.locator(_ROW_BALANCE_SELECTOR).first
            if await balance_el.count() == 0:
                logger.warning("Marcus row {} has no Current balance cell; skipping", index)
                continue
            text = (await balance_el.inner_text() or "").strip()
            balance = parse_balance_text(text)
            balances.append(balance)
            logger.debug("Marcus row {} balance: {}", index, balance)

        return balances

    async def _resolve_activity_url(self, page: Page) -> str:
        """Use the current page when it already shows the account list."""
        try:
            account_list = page.locator(_ACCOUNT_LIST_SELECTOR).first
            await account_list.wait_for(state="visible", timeout=_BALANCE_WAIT_MS)
            return page.url
        except Exception:
            pass

        dashboard_candidates = (
            "https://www.marcus.com/us/en/dashboard",
            "https://www.marcus.com/us/en/accounts",
        )
        for url in dashboard_candidates:
            await page.goto(url, wait_until="domcontentloaded")
            self._raise_if_needs_reauth(page)
            try:
                account_list = page.locator(_ACCOUNT_LIST_SELECTOR).first
                await account_list.wait_for(state="visible", timeout=_BALANCE_WAIT_MS)
                return page.url
            except Exception:
                continue

        return page.url

    async def download_account(
        self,
        page: Page,
        *,
        activity_url: str,
        flow: str,
        download_dir: Path,
    ) -> Path:
        raise NoDownloadError(
            "Marcus aggregated balances use balance scrape; statement downloads are not implemented."
        )

    def _raise_if_needs_reauth(self, page: Page) -> None:
        url = (page.url or "").lower()
        if is_login_url(url, _LOGIN_URL_MARKERS):
            raise NeedsReauthError("Marcus session expired; sign in again.")
