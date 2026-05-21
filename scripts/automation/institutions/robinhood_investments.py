"""Robinhood investment account statement adapter.

The investment side uses the same domain but a different activity view at
``/account/history``. Account statements (CSV/PDF) are reachable from there.
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
    SLUG = "robinhood_investments"
    URL = "https://robinhood.com/account/history"

    def is_session_valid(self, page: Page) -> bool:
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(
                page,
                (
                    "h1:has-text('History')",
                    "h1:has-text('Activity')",
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
            "Export button on Robinhood investment history page",
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
            "CSV option in Robinhood investments export menu",
        )
        return expect_download(page, csv.click, self.download_timeout_ms)
