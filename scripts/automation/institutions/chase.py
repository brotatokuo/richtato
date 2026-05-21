"""Chase statement download adapter.

Assumed flow:
1. Land on the secure accounts overview at ``/web/auth/dashboard``.
2. Open the target account tile, then the "See activity" / "Download account activity" link.
3. Select CSV + current cycle range, submit, capture the download.
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

LOGIN_URL_FRAGMENTS = ("logon", "signin", "auth/login")


class Adapter(InstitutionAdapter):
    SLUG = "chase"
    URL = "https://secure.chase.com/web/auth/dashboard"

    def is_session_valid(self, page: Page) -> bool:
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(
                page,
                (
                    "[data-testid='dashboardTile']",
                    "mds-text:has-text('Accounts')",
                    "button:has-text('Sign out')",
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
                    "[data-testid='dashboardTile']",
                    "a:has-text('See activity')",
                    "a.account-tile",
                ),
            ),
            "primary account tile on Chase dashboard",
        )
        page.wait_for_load_state("networkidle")

        click_or_break(
            first_visible(
                page,
                (
                    "a:has-text('Download account activity')",
                    "a:has-text('Download')",
                    "button:has-text('Download')",
                ),
            ),
            "Download account activity link on Chase",
        )
        page.wait_for_load_state("networkidle")

        file_type = first_visible(
            page, ("select[name='fileType']", "select[name='downloadType']")
        )
        if file_type is not None:
            try:
                file_type.select_option(value="CSV")
            except Exception:
                file_type.select_option(label="Spreadsheet (CSV)")

    def trigger_download(self, page: Page) -> Download:
        submit = require(
            first_visible(
                page,
                (
                    "button:has-text('Download'):not(:has-text('Download account'))",
                    "button[type='submit']:has-text('Download')",
                    "input[type='submit'][value*='Download']",
                ),
            ),
            "Download submit button on Chase",
        )
        return expect_download(page, submit.click, self.download_timeout_ms)
