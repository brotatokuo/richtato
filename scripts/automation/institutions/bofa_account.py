"""BoFA per-account adapter for the new multi-account flow.

Unlike the legacy ``bofa.py`` adapter, this one is not registered by slug. The
runner constructs it per ``AutomationAccount`` and drives it directly. Each
account brings its own activity URL (containing the BoFA ``adx`` token) and
selects a ``flow`` variant (``deposit`` or ``credit_card``) that picks the
correct download-page selectors.

Selectors are best-effort and will need iteration as BoFA's DOM changes.
Initial credit-card selectors are inferred from typical BoFA patterns and
should be confirmed during a headed verification run.
"""

from __future__ import annotations

from playwright.sync_api import Download, Page

from scripts.automation.config import AutomationAccount
from scripts.automation.errors import DomBroken
from scripts.automation.institutions._helpers import (
    assert_not_on_login,
    click_or_break,
    expect_download,
    first_visible,
    require,
)

LOGIN_URL_FRAGMENTS = ("sign-in", "login", "signin")

DEFAULT_NAV_TIMEOUT_MS = 30_000
DEFAULT_DOWNLOAD_TIMEOUT_MS = 90_000


class BofaAccountAdapter:
    """Drive a single BoFA account's activity/download page.

    Constructed per ``AutomationAccount`` so multiple accounts can be driven
    inside the same browser context (one per ``LoginSession``).
    """

    nav_timeout_ms: int = DEFAULT_NAV_TIMEOUT_MS
    download_timeout_ms: int = DEFAULT_DOWNLOAD_TIMEOUT_MS

    def __init__(self, account: AutomationAccount) -> None:
        self.account = account

    @property
    def slug(self) -> str:
        return self.account.slug

    @property
    def url(self) -> str:
        return self.account.activity_url

    @property
    def flow(self) -> str:
        return self.account.flow

    def is_session_valid(self, page: Page) -> bool:
        """Return True when the post-goto page looks like an authenticated view.

        Avoids reaching into account-specific markers because deposit and
        credit-card pages render very different chrome. The only firm signal
        is that BoFA did not redirect us to a login screen.
        """

        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in LOGIN_URL_FRAGMENTS):
            return False
        if (
            first_visible(
                page,
                (
                    "a:has-text('Sign Out')",
                    "button:has-text('Sign Out')",
                    "a[href*='signout']",
                    "a[href*='sign-out']",
                    "[id*='signout']",
                    "[data-testid='sign-out']",
                ),
                timeout_ms=2_000,
            )
            is not None
        ):
            return True
        return (
            first_visible(
                page,
                (
                    "a:has-text('Download')",
                    "a:has-text('Download account activity')",
                    "button:has-text('Download')",
                ),
                timeout_ms=2_000,
            )
            is not None
        )

    def navigate_to_export(self, page: Page) -> None:
        """Make sure we have not been bounced to login.

        The runner already navigates to ``activity_url`` before calling this,
        so there is no further click-through. We only assert the page state
        and dispatch by flow for any pre-download UI a variant needs.
        """

        assert_not_on_login(page, LOGIN_URL_FRAGMENTS)
        if self.flow == "deposit":
            self._prepare_deposit(page)
        elif self.flow == "credit_card":
            self._prepare_credit_card(page)
        else:
            raise DomBroken(
                f"Unsupported flow {self.flow!r} for BoFA account {self.slug!r}"
            )

    def trigger_download(self, page: Page) -> Download:
        if self.flow == "deposit":
            return self._deposit_download(page)
        if self.flow == "credit_card":
            return self._credit_card_download(page)
        raise DomBroken(
            f"Unsupported flow {self.flow!r} for BoFA account {self.slug!r}"
        )

    def _prepare_deposit(self, page: Page) -> None:
        click_or_break(
            first_visible(
                page,
                (
                    "a:has-text('Download')",
                    "button:has-text('Download')",
                    "a[aria-label*='Download']",
                ),
            ),
            f"Download link on BoA deposit activity page ({self.slug})",
        )
        page.wait_for_load_state("domcontentloaded")

        # Transaction period — select "Current transactions" (most recent activity).
        txn_period = first_visible(
            page,
            (
                "select#select_txnPeriod",
                "select[name='payload.txnSearchCriteria.txnPeriod']",
            ),
        )
        if txn_period is not None:
            try:
                txn_period.select_option(value="Current transactions")
            except Exception:
                pass

        # File type — value "csv" = "Microsoft Excel Format" (BofA's label for CSV).
        file_type = first_visible(
            page,
            (
                "select#select_fileType",
                "select[name='payload.txnSearchCriteria.fileType']",
                "select[name='filetype']",
                "select#fileFormat",
                "select#filetype",
            ),
        )
        if file_type is not None:
            try:
                file_type.select_option(value="csv")
            except Exception:
                file_type.select_option(label="Microsoft Excel Format")

    def _deposit_download(self, page: Page) -> Download:
        submit = require(
            first_visible(
                page,
                (
                    "form#downloadTxnForm button[type='submit']",
                    "button:has-text('Download')",
                    "button:has-text('Download Transactions')",
                    "input[type='submit'][value*='Download']",
                    "button[type='submit']",
                    "button#downloadButton",
                    "input[type='submit']",
                ),
            ),
            f"Download submit button on BoA deposit page ({self.slug})",
        )
        return expect_download(page, submit.click, self.download_timeout_ms)

    def _prepare_credit_card(self, page: Page) -> None:
        click_or_break(
            first_visible(
                page,
                (
                    "a:has-text('Download account activity')",
                    "a:has-text('Download')",
                    "button:has-text('Download account activity')",
                    "button:has-text('Download')",
                    "a[aria-label*='Download']",
                ),
            ),
            f"Download link on BoA credit card activity page ({self.slug})",
        )
        page.wait_for_load_state("domcontentloaded")

        file_type = first_visible(
            page,
            (
                "select[name='filetype']",
                "select#fileFormat",
                "select#filetype",
                "select[name='fileFormat']",
            ),
        )
        if file_type is not None:
            try:
                file_type.select_option(value="csv")
            except Exception:
                try:
                    file_type.select_option(label="Comma Separated Values (.csv)")
                except Exception:
                    file_type.select_option(label="Microsoft Excel (.csv)")

    def _credit_card_download(self, page: Page) -> Download:
        submit = require(
            first_visible(
                page,
                (
                    "button:has-text('Download Transactions')",
                    "button:has-text('Download')",
                    "input[type='submit'][value*='Download']",
                    "button[type='submit']",
                    "button#downloadButton",
                    "input[type='submit']",
                ),
            ),
            f"Download submit button on BoA credit card page ({self.slug})",
        )
        return expect_download(page, submit.click, self.download_timeout_ms)
