"""American Express statement download adapter.

Note: Amex aggressively detects automated browsers. Headless runs may be
rejected with CAPTCHA prompts. Re-bootstrap from the desktop's real browser
when sessions invalidate and consider a longer download timeout.
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

LOGIN_URL_FRAGMENTS = ("login", "logon", "auth")


class Adapter(InstitutionAdapter):
    SLUG = "amex"
    URL = "https://global.americanexpress.com/activity/recent"
    download_timeout_ms = 120_000

    def is_session_valid(self, page: Page) -> bool:
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(
                page,
                (
                    "[data-testid='activity-table']",
                    "a:has-text('Statements & Activity')",
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
                    "a:has-text('Download')",
                    "[data-testid='download-activity']",
                ),
            ),
            "Download button on Amex activity page",
        )
        page.wait_for_load_state("networkidle")

        csv_radio = first_visible(
            page,
            (
                "label:has-text('CSV')",
                "label:has-text('Comma Separated')",
                "input[value='csv']",
            ),
        )
        if csv_radio is not None:
            csv_radio.click()

    def trigger_download(self, page: Page) -> Download:
        submit = require(
            first_visible(
                page,
                (
                    "button:has-text('Download'):not(:disabled)",
                    "button[type='submit']:has-text('Download')",
                ),
            ),
            "final Download submit button on Amex",
        )
        return expect_download(page, submit.click, self.download_timeout_ms)
