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

from scripts.bank_sync.errors import (
    AgentError,
    DomBrokenError,
    FAILURE_KIND_PRIORITY,
    NeedsReauthError,
    NoDownloadError,
    failure_kind_for,
)
from scripts.bank_sync.institutions.base import BaseInstitutionAdapter, DiscoveredAccount
from scripts.bank_sync.playwright_helpers import (
    DOWNLOAD_TIMEOUT_MS,
    html_body_suggests_reauth,
    is_login_url,
    raise_after_selector_failure,
    wait_for_user_login,
)

_HOME = "https://www.bankofamerica.com/"
_LOGGED_IN_URLS = ("/myaccountdetails/", "/myaccounts", "/myaccountoverview")
_LOGIN_URL_MARKERS = ("signin", "login")
_DOWNLOAD_FORM_URL = (
    "https://secure.bankofamerica.com/ogateway/addapi/v1/download/form/transaction"
)
_DEFAULT_TXN_PERIOD = "Current transactions"
_DEFAULT_FILE_TYPE = "csv"


def _account_token_from_url(activity_url: str) -> str:
    match = re.search(r"[?&]adx=([^&#]+)", activity_url)
    if not match:
        raise NoDownloadError("Activity URL missing adx account token.")
    return match.group(1)


def _filename_from_response_headers(headers: dict[str, str]) -> str:
    disposition = headers.get("content-disposition", "")
    match = re.search(r'filename="?([^";]+)"?', disposition, re.I)
    if match:
        return match.group(1).strip()
    return "statement.csv"


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
        """Best-effort scan of the BoFA "My Accounts" page."""

        accounts: list[DiscoveredAccount] = []
        try:
            await page.goto(
                "https://secure.bankofamerica.com/myaccountdetails/signin/overview.go",
                wait_until="domcontentloaded",
            )
        except Exception:
            logger.debug("BoFA overview navigation failed; falling back to current page")

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

    async def _open_download_form(self, page: Page) -> None:
        """Reveal BoFA's ``#downloadTxnForm`` download panel if needed."""
        form = page.locator("#downloadTxnForm")
        try:
            await form.wait_for(state="visible", timeout=5_000)
            return
        except Exception:
            pass

        try:
            await page.get_by_role("button", name=re.compile(r"download", re.I)).first.click()
            await form.wait_for(state="visible", timeout=DOWNLOAD_TIMEOUT_MS)
        except Exception as exc:
            await raise_after_selector_failure(
                page,
                exc,
                login_markers=_LOGIN_URL_MARKERS,
                dom_context="BoFA activity page missing download control",
            )

    async def _select_download_options(self, page: Page) -> None:
        """Fill the transaction period + file type dropdowns on the download form."""
        period_select = page.locator("#select_txnPeriod")
        try:
            await period_select.wait_for(state="visible", timeout=DOWNLOAD_TIMEOUT_MS)
        except Exception as exc:
            await raise_after_selector_failure(
                page,
                exc,
                login_markers=_LOGIN_URL_MARKERS,
                dom_context="BoFA download form missing transaction period selector",
            )

        period_value = "Current transactions"
        if await period_select.locator(f'option[value="{period_value}"]').count() == 0:
            period_value = await period_select.evaluate(
                """select => {
                    const option = [...select.options].find(
                        o => o.value && o.value !== 'custom range'
                    );
                    return option ? option.value : '';
                }"""
            )
            if not period_value:
                raise DomBrokenError(
                    "BoFA download form has no selectable transaction period."
                )

        await period_select.select_option(value=period_value)
        await page.locator("#select_fileType").select_option(value="csv")

    async def _click_download_submit(self, page: Page) -> None:
        submit = page.locator(
            "form#downloadTxnForm button[type='submit'], "
            "button[form='downloadTxnForm'][type='submit']"
        )
        if await submit.count():
            await submit.first.click()
            return
        try:
            await page.get_by_role("button", name=re.compile(r"download", re.I)).last.click()
        except Exception as exc:
            await raise_after_selector_failure(
                page,
                exc,
                login_markers=_LOGIN_URL_MARKERS,
                dom_context="BoFA download form missing submit control",
            )

    async def _download_via_form_post(
        self,
        page: Page,
        *,
        activity_url: str,
        download_dir: Path,
    ) -> Path:
        """POST BoFA's download form using the authenticated browser session."""
        response = await page.context.request.post(
            _DOWNLOAD_FORM_URL,
            form={
                "payload.accountToken": _account_token_from_url(activity_url),
                "payload.locale": "en-us",
                "payload.txnSearchCriteria.txnPeriod": _DEFAULT_TXN_PERIOD,
                "payload.txnSearchCriteria.fileType": _DEFAULT_FILE_TYPE,
            },
            headers={"Referer": activity_url},
            timeout=DOWNLOAD_TIMEOUT_MS,
        )
        if not response.ok:
            raise NoDownloadError(f"BoFA download POST failed: HTTP {response.status}")

        body = await response.body()
        if not body:
            raise NoDownloadError("BoFA download POST returned an empty body.")

        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type.lower() and b"<html" in body[:1000].lower():
            if html_body_suggests_reauth(body):
                raise NeedsReauthError(
                    "BoFA download POST returned a sign-in page instead of CSV."
                )
            raise DomBrokenError(
                "BoFA download POST returned an HTML error page instead of CSV."
            )

        filename = _filename_from_response_headers(response.headers)
        target = download_dir / filename
        target.write_bytes(body)
        return target

    async def _download_via_ui(self, page: Page, *, download_dir: Path) -> Path:
        """Fill the on-page download modal and capture the popup download."""
        await self._open_download_form(page)
        await self._select_download_options(page)

        async with page.expect_popup(timeout=DOWNLOAD_TIMEOUT_MS) as popup_info:
            await self._click_download_submit(page)
        popup = await popup_info.value
        try:
            download = await popup.wait_for_event("download", timeout=DOWNLOAD_TIMEOUT_MS)
            suggested = download.suggested_filename or "statement.csv"
            target = download_dir / suggested
            await download.save_as(str(target))
            return target
        finally:
            await popup.close()

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
        if is_login_url(url, _LOGIN_URL_MARKERS):
            raise NeedsReauthError(f"BoFA redirected to sign-in: {url}")

        download_dir.mkdir(parents=True, exist_ok=True)
        errors: list[Exception] = []

        for attempt in (
            lambda: self._download_via_form_post(
                page, activity_url=activity_url, download_dir=download_dir
            ),
            lambda: self._download_via_ui(page, download_dir=download_dir),
        ):
            try:
                target = await attempt()
            except NeedsReauthError:
                raise
            except Exception as exc:
                errors.append(exc)
                logger.debug("BoFA download attempt failed: {}", exc)
                continue
            else:
                logger.info("Downloaded {}", target)
                return target

        if not errors:
            raise NoDownloadError("BoFA download did not produce a file.")

        for exc in errors:
            if isinstance(exc, NeedsReauthError):
                raise exc

        primary = min(
            errors,
            key=lambda exc: FAILURE_KIND_PRIORITY[failure_kind_for(exc)],
        )
        if isinstance(primary, AgentError):
            raise primary
        raise NoDownloadError("; ".join(str(exc) for exc in errors))
