"""Robinhood Spending / Banking statement adapter.

Robinhood's banking ("Cash") product surfaces transactions under
``/account/banking``. Activity export is via an "Export" menu that yields CSV.
"""

from __future__ import annotations

from playwright.sync_api import Download, Page

from scripts.automation.institutions._helpers import (
    assert_not_on_login,
    click_or_break,
    expect_download,
    first_visible,
    require,
)
from scripts.automation.institutions.base import InstitutionAdapter

LOGIN_URL_FRAGMENTS = ("login", "signin", "auth")


class Adapter(InstitutionAdapter):
    SLUG = "robinhood_bank"
    URL = "https://robinhood.com/account/banking"

    def is_session_valid(self, page: Page) -> bool:
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(
                page,
                (
                    "h1:has-text('Spending')",
                    "h1:has-text('Banking')",
                    "button:has-text('Log out')",
                ),
                timeout_ms=8_000,
            )
            is not None
        )

    def navigate_to_export(self, page: Page) -> None:
        assert_not_on_login(page, LOGIN_URL_FRAGMENTS)
        click_or_break(
            first_visible(
                page,
                (
                    "button:has-text('Export')",
                    "button:has-text('Download')",
                    "[aria-label*='Export']",
                ),
            ),
            "Export button on Robinhood banking page",
        )

    def trigger_download(self, page: Page) -> Download:
        csv = require(
            first_visible(
                page,
                (
                    "button:has-text('CSV')",
                    "a:has-text('Download CSV')",
                    "li[role='menuitem']:has-text('CSV')",
                ),
            ),
            "CSV option in Robinhood banking export menu",
        )
        return expect_download(page, csv.click, self.download_timeout_ms)
