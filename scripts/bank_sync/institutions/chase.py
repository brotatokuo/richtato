"""Chase adapter (cookie-only, no stored credentials)."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

from loguru import logger
from playwright.async_api import BrowserContext, Page

from scripts.bank_sync.errors import NeedsReauthError, NoDownloadError
from scripts.bank_sync.institutions.base import BaseInstitutionAdapter, DiscoveredAccount
from scripts.bank_sync.playwright_helpers import (
    DOWNLOAD_TIMEOUT_MS,
    download_to_dir,
    wait_for_user_login,
)

_HOME = "https://secure.chase.com/web/auth/dashboard"
_LOGGED_IN_URLS = (
    "/web/auth/dashboard",
    "/secure/dashboard",
    "/cmo/account/dashboard",
)


class ChaseAdapter(BaseInstitutionAdapter):
    slug = "chase"
    institution_display_name = "Chase"
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
        """Walk the Chase dashboard for account tiles with activity links."""

        accounts: list[DiscoveredAccount] = []
        anchors = await page.query_selector_all("a[href*='accountId']")
        seen: set[str] = set()
        for anchor in anchors:
            href = (await anchor.get_attribute("href") or "").strip()
            if not href:
                continue
            absolute = urljoin(page.url, href)
            m = re.search(r"[?&]accountId=([^&#]+)", absolute)
            if not m:
                continue
            token = m.group(1)
            if token in seen:
                continue
            seen.add(token)
            name = (await anchor.inner_text() or "").strip() or "Chase account"
            flow = "credit_card" if any(
                kw in name.lower() for kw in ("card", "credit", "visa", "mastercard", "freedom", "sapphire")
            ) else "deposit"
            accounts.append(
                DiscoveredAccount(
                    detected_account_name=name[:255],
                    activity_url=absolute,
                    external_account_token=token,
                    flow=flow,
                )
            )

        logger.info("Chase discovery surfaced {} account(s)", len(accounts))
        return accounts

    async def download_account(
        self,
        page: Page,
        *,
        activity_url: str,
        flow: str,
        download_dir: Path,
    ) -> Path:
        await page.goto(activity_url, wait_until="domcontentloaded", timeout=DOWNLOAD_TIMEOUT_MS)
        url = page.url or ""
        if "logon" in url or "auth/logon" in url:
            raise NeedsReauthError(f"Chase redirected to sign-in: {url}")

        async def trigger() -> None:
            # Chase's "Download account activity" CTA. Selectors are
            # text-based to absorb minor DOM tweaks; tests in production
            # will tighten these as we observe real failures.
            await page.get_by_role("button", name=re.compile(r"download (account )?activity", re.I)).click()
            await page.get_by_label(re.compile(r"csv|comma", re.I)).check()
            await page.get_by_role("button", name=re.compile(r"^download$", re.I)).click()

        try:
            return await download_to_dir(page, download_dir=download_dir, trigger=trigger)
        except Exception as exc:
            raise NoDownloadError(f"Chase download did not produce a file: {exc}") from exc
