"""Bank of America adapter.

Cookie-only design: this adapter never receives or stores a username or
password. The first sign-in always happens in a headed Chromium window the
user interacts with directly.
"""

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

_HOME = "https://www.bankofamerica.com/"
_LOGGED_IN_URLS = ("/myaccountdetails/", "/myaccounts", "/myaccountoverview")


class BofaAdapter(BaseInstitutionAdapter):
    slug = "bofa"
    institution_display_name = "Bank of America"
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
        """Best-effort scan of the BoFA "My Accounts" page.

        The page lists deposit and credit cards as ``<a>`` tags whose href
        carries the ``adx`` token. We capture the visible text as the
        detected name and infer the ``flow`` from the section header.
        """

        accounts: list[DiscoveredAccount] = []
        try:
            await page.goto(
                "https://secure.bankofamerica.com/myaccountdetails/signin/overview.go",
                wait_until="domcontentloaded",
            )
        except Exception:
            # Some users land directly on /myaccounts - that's fine; we'll
            # scan whatever the current URL is.
            logger.debug("BoFA overview navigation failed; falling back to current page")

        # Pull every link that points at the activity page and carries an
        # ``adx`` token; those are the per-account "View activity" anchors.
        anchors = await page.query_selector_all("a[href*='adx=']")
        seen_tokens: set[str] = set()
        for anchor in anchors:
            href = (await anchor.get_attribute("href") or "").strip()
            if not href:
                continue
            absolute = urljoin(page.url, href)
            m = re.search(r"[?&]adx=([^&#]+)", absolute)
            if not m:
                continue
            token = m.group(1)
            if token in seen_tokens:
                continue
            seen_tokens.add(token)
            name = (await anchor.inner_text() or "").strip() or "Bank of America account"
            flow = "credit_card" if any(
                kw in name.lower() for kw in ("card", "credit", "visa", "mastercard")
            ) else "deposit"
            accounts.append(
                DiscoveredAccount(
                    detected_account_name=name[:255],
                    activity_url=absolute,
                    external_account_token=token,
                    flow=flow,
                )
            )

        logger.info("BoFA discovery surfaced {} account(s)", len(accounts))
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
        if "signin" in url or "login" in url:
            raise NeedsReauthError(f"BoFA redirected to sign-in: {url}")

        async def trigger() -> None:
            # BoFA's download CTA: a "Download" button followed by a
            # "Comma-Delimited (.csv)" radio + "Download" submit. We use
            # text/role selectors so DOM tweaks don't fully break the flow.
            await page.get_by_role("button", name=re.compile(r"download", re.I)).first.click()
            await page.get_by_label(re.compile(r"comma.+delimited", re.I)).check()
            await page.get_by_role("button", name=re.compile(r"download", re.I)).last.click()

        try:
            return await download_to_dir(page, download_dir=download_dir, trigger=trigger)
        except Exception as exc:
            raise NoDownloadError(f"BoFA download did not produce a file: {exc}") from exc
