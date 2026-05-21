"""Bank of America statement download adapter.

Assumed flow (subject to BoA DOM changes):
1. Land on the secure dashboard; a logged-in session shows the accounts overview.
2. Click into the target account, then open the "Download" link near the activity tab.
3. Choose the CSV format and trigger the download.
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

LOGIN_URL_FRAGMENTS = ("sign-in", "login", "signin")


class Adapter(InstitutionAdapter):
    SLUG = "bofa"
    URL = (
        "https://secure.bankofamerica.com/myaccounts/brain/redirect.go?source=overview"
    )

    def is_session_valid(self, page: Page) -> bool:
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(
                page,
                (
                    "text=Accounts Overview",
                    "[data-testid='account-overview']",
                    "a:has-text('Sign Out')",
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
                    "a[data-track-name='Account-Name-Link']",
                    "a.AccountName",
                    "a:has-text('Adv Plus')",
                ),
            ),
            "primary account link on BoA overview",
        )
        page.wait_for_load_state("networkidle")

        click_or_break(
            first_visible(
                page,
                (
                    "a:has-text('Download')",
                    "button:has-text('Download')",
                    "a[aria-label*='Download']",
                ),
            ),
            "Download link on BoA account activity page",
        )
        page.wait_for_load_state("networkidle")

        file_type = first_visible(
            page,
            (
                "select[name='filetype']",
                "select#fileFormat",
            ),
        )
        if file_type is not None:
            try:
                file_type.select_option(value="csv")
            except Exception:
                file_type.select_option(label="Comma Separated Values (.csv)")

    def trigger_download(self, page: Page) -> Download:
        submit = require(
            first_visible(
                page,
                (
                    "button:has-text('Download Transactions')",
                    "input[type='submit'][value*='Download']",
                    "button#downloadButton",
                ),
            ),
            "Download submit button on BoA",
        )
        return expect_download(page, submit.click, self.download_timeout_ms)
