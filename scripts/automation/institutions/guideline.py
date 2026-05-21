"""Guideline 401(k) statement adapter.

Guideline exposes contribution history at ``/dashboard/transactions``. The
export control is usually a "Download CSV" button.
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

LOGIN_URL_FRAGMENTS = ("login", "sign-in", "signin", "auth")


class Adapter(InstitutionAdapter):
    SLUG = "guideline"
    URL = "https://app.guideline.com/dashboard/transactions"

    def is_session_valid(self, page: Page) -> bool:
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(
                page,
                (
                    "h1:has-text('Transactions')",
                    "a:has-text('Log out')",
                    "[data-testid='transactions']",
                ),
                timeout_ms=8_000,
            )
            is not None
        )

    def navigate_to_export(self, page: Page) -> None:
        assert_not_on_login(page, LOGIN_URL_FRAGMENTS)
        export_button = first_visible(
            page,
            (
                "button:has-text('Download CSV')",
                "button:has-text('Export')",
                "a:has-text('Download')",
            ),
        )
        if export_button is None:
            click_or_break(
                first_visible(page, ("button:has-text('Download')",)),
                "Download button on Guideline transactions page",
            )

    def trigger_download(self, page: Page) -> Download:
        submit = require(
            first_visible(
                page,
                (
                    "button:has-text('Download CSV')",
                    "a:has-text('Download CSV')",
                    "button:has-text('CSV')",
                ),
            ),
            "Download CSV button on Guideline",
        )
        return expect_download(page, submit.click, self.download_timeout_ms)
