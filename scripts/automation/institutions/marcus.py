"""Marcus by Goldman Sachs statement download adapter.

Marcus exposes recent activity behind ``/transactions`` and supports CSV export
through the activity-page kebab menu. Sessions tend to last 60-90 days.
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

LOGIN_URL_FRAGMENTS = ("login", "sign-in", "signin")


class Adapter(InstitutionAdapter):
    SLUG = "marcus"
    URL = "https://www.marcus.com/us/en/account-summary/transactions"

    def is_session_valid(self, page: Page) -> bool:
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(
                page,
                (
                    "h1:has-text('Transactions')",
                    "a:has-text('Sign out')",
                    "[data-testid='transactions-table']",
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
                    "button:has-text('Download')",
                    "button:has-text('Export')",
                    "[aria-label*='Download']",
                ),
            ),
            "Download/Export button on Marcus transactions page",
        )

    def trigger_download(self, page: Page) -> Download:
        submit = require(
            first_visible(
                page,
                (
                    "button:has-text('Download CSV')",
                    "a:has-text('CSV')",
                    "li[role='menuitem']:has-text('CSV')",
                ),
            ),
            "CSV option in Marcus download menu",
        )
        return expect_download(page, submit.click, self.download_timeout_ms)
