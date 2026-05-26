"""Chase adapter (cookie-only, no stored credentials)."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

from loguru import logger
from playwright.async_api import BrowserContext, Locator, Page

from scripts.bank_sync.errors import NeedsReauthError
from scripts.bank_sync.institutions.base import (
    BaseInstitutionAdapter,
    DiscoveredAccount,
)
from scripts.bank_sync.playwright_helpers import (
    DOWNLOAD_TIMEOUT_MS,
    download_to_dir,
    is_login_url,
    raise_after_selector_failure,
    wait_for_user_login,
)

_HOME = "https://secure.chase.com/web/auth/dashboard"
_LOGGED_IN_URLS = (
    "/web/auth/dashboard",
    "/secure/dashboard",
    "/cmo/account/dashboard",
)
_LOGIN_URL_MARKERS = ("logon", "auth/logon")
_DIRECT_DOWNLOAD_MARKER = "downloadaccounttransactions"
_CREDIT_CARD_NAME_KEYWORDS = (
    "card",
    "credit",
    "visa",
    "mastercard",
    "freedom",
    "sapphire",
)
_MDS_SELECT_WAIT_MS = 15_000

_ACCOUNT_ID_QUERY_RE = re.compile(r"[?&]accountId=([^&#]+)", re.I)
_DIRECT_DOWNLOAD_PARAMS_RE = re.compile(
    r"downloadAccountTransactions[^;]*;params=[^,]+,[^,]+,(\d+)",
    re.I,
)
_DIRECT_DOWNLOAD_FRAGMENT_RE = re.compile(r";params=[^,]+,[^,]+,(\d+)", re.I)


def is_direct_download_url(url: str) -> bool:
    """Return True when ``url`` targets Chase's Direct Download page."""
    return _DIRECT_DOWNLOAD_MARKER in (url or "").lower()


def account_token_from_url(url: str) -> str:
    """Extract the Chase account id token from activity or Direct Download URLs."""
    if not url:
        return ""
    for pattern in (
        _DIRECT_DOWNLOAD_PARAMS_RE,
        _DIRECT_DOWNLOAD_FRAGMENT_RE,
        _ACCOUNT_ID_QUERY_RE,
    ):
        match = pattern.search(url)
        if match:
            return match.group(1)
    return ""


def infer_flow_from_name(name: str) -> str:
    lowered = (name or "").lower()
    if any(kw in lowered for kw in _CREDIT_CARD_NAME_KEYWORDS):
        return "credit_card"
    return "deposit"


def _prefer_activity_url(current: str, candidate: str) -> str:
    if not current:
        return candidate
    if is_direct_download_url(candidate) and not is_direct_download_url(current):
        return candidate
    return current


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
        """Walk the Chase dashboard for per-account activity or Direct Download links."""

        by_token: dict[str, DiscoveredAccount] = {}

        def upsert(
            *,
            token: str,
            name: str,
            activity_url: str,
        ) -> None:
            if not token:
                return
            flow = infer_flow_from_name(name)
            existing = by_token.get(token)
            if existing is None:
                by_token[token] = DiscoveredAccount(
                    detected_account_name=name[:255],
                    activity_url=activity_url,
                    external_account_token=token,
                    flow=flow,
                )
                return
            preferred_url = _prefer_activity_url(existing.activity_url, activity_url)
            preferred_name = existing.detected_account_name
            if name and name != "Chase account":
                preferred_name = name[:255]
            by_token[token] = DiscoveredAccount(
                detected_account_name=preferred_name,
                activity_url=preferred_url,
                external_account_token=token,
                flow=flow,
            )

        anchors = await page.query_selector_all(
            "a[href*='accountId'], a[href*='downloadAccountTransactions']"
        )
        for anchor in anchors:
            href = (await anchor.get_attribute("href") or "").strip()
            if not href:
                continue
            absolute = urljoin(page.url, href)
            token = account_token_from_url(absolute)
            if not token:
                continue
            name = (await anchor.inner_text() or "").strip() or "Chase account"
            upsert(token=token, name=name, activity_url=absolute)

        for anchor in await page.query_selector_all("a[href]"):
            href = (await anchor.get_attribute("href") or "").strip()
            if not href or "downloadAccountTransactions" not in href:
                continue
            absolute = urljoin(page.url, href)
            token = account_token_from_url(absolute)
            if not token:
                continue
            name = (await anchor.inner_text() or "").strip() or "Chase account"
            upsert(token=token, name=name, activity_url=absolute)

        accounts = list(by_token.values())
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
        await page.goto(
            activity_url, wait_until="domcontentloaded", timeout=DOWNLOAD_TIMEOUT_MS
        )
        self._raise_if_needs_reauth(page)

        if is_direct_download_url(activity_url) or await self._page_has_direct_download(
            page
        ):
            return await download_to_dir(
                page,
                download_dir=download_dir,
                trigger=lambda: self._trigger_direct_download(page, activity_url),
            )

        if await self._try_open_direct_download_from_activity(page):
            return await download_to_dir(
                page,
                download_dir=download_dir,
                trigger=lambda: self._trigger_direct_download(page, activity_url),
            )

        return await download_to_dir(
            page,
            download_dir=download_dir,
            trigger=lambda: self._trigger_legacy_download(page),
        )

    def _raise_if_needs_reauth(self, page: Page) -> None:
        url = page.url or ""
        if is_login_url(url, _LOGIN_URL_MARKERS):
            raise NeedsReauthError(f"Chase redirected to sign-in: {url}")

    async def _page_has_direct_download(self, page: Page) -> bool:
        try:
            panel = page.locator("#downloadAccountActivity")
            await panel.wait_for(state="visible", timeout=5_000)
            return True
        except Exception:
            return is_direct_download_url(page.url or "")

    async def _try_open_direct_download_from_activity(self, page: Page) -> bool:
        try:
            await page.get_by_role(
                "button", name=re.compile(r"download (account )?activity", re.I)
            ).click(timeout=8_000)
            await page.locator("#downloadAccountActivity").wait_for(
                state="visible", timeout=_MDS_SELECT_WAIT_MS
            )
            return True
        except Exception:
            return await self._page_has_direct_download(page)

    async def _trigger_direct_download(self, page: Page, activity_url: str) -> None:
        try:
            await page.locator("#downloadAccountActivity").wait_for(
                state="visible", timeout=_MDS_SELECT_WAIT_MS
            )
            token = account_token_from_url(activity_url)
            if token:
                await self._select_mds_option(
                    page,
                    select_id="account-selector",
                    value=token,
                )
            await self._select_mds_option(
                page,
                select_id="downloadFileTypeOption",
                value="CSV",
            )
            await self._select_mds_option(
                page,
                select_id="downloadActivityOptionId",
                value="last24monthsOption",
            )
            await self._click_mds_button(page, button_id="download")
        except Exception as exc:
            await raise_after_selector_failure(
                page,
                exc,
                login_markers=_LOGIN_URL_MARKERS,
                dom_context="Chase Direct Download page missing expected controls",
            )

    async def _trigger_legacy_download(self, page: Page) -> None:
        try:
            await page.get_by_role(
                "button", name=re.compile(r"download (account )?activity", re.I)
            ).click()
            await page.get_by_label(re.compile(r"csv|comma", re.I)).check()
            await page.get_by_role(
                "button", name=re.compile(r"^download$", re.I)
            ).click()
        except Exception as exc:
            await raise_after_selector_failure(
                page,
                exc,
                login_markers=_LOGIN_URL_MARKERS,
                dom_context="Chase activity page missing download controls",
            )

    async def _select_mds_option(
        self,
        page: Page,
        *,
        select_id: str,
        value: str,
    ) -> None:
        host = page.locator(f"mds-select#{select_id}")
        await host.wait_for(state="attached", timeout=_MDS_SELECT_WAIT_MS)
        current = (await host.get_attribute("value") or "").strip()
        if current == value:
            return

        combobox = host.locator(
            "button[role='combobox'], button.mds-select__select"
        ).first
        await combobox.click(timeout=_MDS_SELECT_WAIT_MS)
        option = page.locator(
            f"mds-select#{select_id} mds-select-option[value='{value}']"
        ).first
        try:
            await option.wait_for(state="attached", timeout=3_000)
            await option.click(timeout=_MDS_SELECT_WAIT_MS)
            return
        except Exception:
            pass

        option_by_label = page.locator(
            f"mds-select#{select_id} mds-select-option"
        ).filter(has=page.locator(f"[value='{value}']"))
        if await option_by_label.count() > 0:
            await option_by_label.first.click(timeout=_MDS_SELECT_WAIT_MS)
            return

        await page.evaluate(
            """({ selectId, value }) => {
                const host = document.querySelector(`mds-select#${selectId}`);
                if (!host) return;
                host.value = value;
                host.dispatchEvent(new Event('change', { bubbles: true }));
                const hidden = host.querySelector('input[type="hidden"][slot="form-associated-input"]');
                if (hidden) hidden.value = value;
                const option = host.querySelector(`mds-select-option[value="${value}"]`);
                if (option) option.selected = true;
            }""",
            {"selectId": select_id, "value": value},
        )

    async def _click_mds_button(self, page: Page, *, button_id: str) -> None:
        host: Locator = page.locator(f"mds-button#{button_id}")
        await host.wait_for(state="attached", timeout=_MDS_SELECT_WAIT_MS)
        inner = host.locator("button").first
        try:
            await inner.click(timeout=_MDS_SELECT_WAIT_MS)
            return
        except Exception:
            pass
        await page.locator(f"#{button_id}").click(timeout=_MDS_SELECT_WAIT_MS)
