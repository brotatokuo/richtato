"""Fidelity statement / transaction history download adapter.

Fidelity lets logged-in users export CSV from the activity / history page at
``/ftgw/digital/portfolio/activity``. Sessions are typically long-lived.
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

LOGIN_URL_FRAGMENTS = ("login", "auth", "signin")


class Adapter(InstitutionAdapter):
    SLUG = "fidelity"
    URL = "https://digital.fidelity.com/ftgw/digital/portfolio/activity"

    def is_session_valid(self, page: Page) -> bool:
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(
                page,
                (
                    "h1:has-text('Activity')",
                    "h1:has-text('History')",
                    "button:has-text('Log Out')",
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
                    "a:has-text('Download')",
                ),
            ),
            "Download/Export control on Fidelity activity page",
        )

    def trigger_download(self, page: Page) -> Download:
        csv_option = require(
            first_visible(
                page,
                (
                    "button:has-text('CSV')",
                    "a:has-text('Comma Separated')",
                    "li[role='menuitem']:has-text('CSV')",
                ),
            ),
            "CSV option in Fidelity download menu",
        )
        return expect_download(page, csv_option.click, self.download_timeout_ms)
