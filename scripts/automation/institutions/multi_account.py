"""Per-account adapters for the DB-driven runner across multiple banks.

The DB-driven runner ([scripts.automation.runner.run_db]) drives one
``BankAccountLink`` at a time using its decrypted ``activity_url``. The
``BofaAccountAdapter`` already proves the pattern; this module extends it
to additional institutions with conservative selector defaults.

Each adapter class lives behind :func:`get_account_adapter` so the runner
can construct one per ``DBAccount`` without hard-coding institution
branches.
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
from scripts.automation.institutions.bofa_account import BofaAccountAdapter

DEFAULT_NAV_TIMEOUT_MS = 30_000
DEFAULT_DOWNLOAD_TIMEOUT_MS = 90_000


class _BaseAccountAdapter:
    """Shared scaffolding for per-account adapters across institutions.

    Subclasses set ``LOGIN_URL_FRAGMENTS`` and provide selectors via the
    template methods below. The runner only ever interacts with the public
    methods (``slug``, ``url``, ``flow``, ``is_session_valid``,
    ``navigate_to_export``, ``trigger_download``) so behaviour stays
    consistent with :class:`BofaAccountAdapter`.
    """

    LOGIN_URL_FRAGMENTS: tuple[str, ...] = ("sign-in", "login", "signin")
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
        page.wait_for_load_state("domcontentloaded")
        if any(fragment in page.url.lower() for fragment in self.LOGIN_URL_FRAGMENTS):
            return False
        return (
            first_visible(page, self._authed_indicators(), timeout_ms=2_000) is not None
        )

    def navigate_to_export(self, page: Page) -> None:
        assert_not_on_login(page, self.LOGIN_URL_FRAGMENTS)
        click_or_break(
            first_visible(page, self._download_link_selectors()),
            f"Download link for {self.slug}",
        )
        page.wait_for_load_state("domcontentloaded")
        self._configure_download_form(page)

    def trigger_download(self, page: Page) -> Download:
        submit = require(
            first_visible(page, self._submit_button_selectors()),
            f"Download submit button for {self.slug}",
        )
        return expect_download(page, submit.click, self.download_timeout_ms)

    # Subclass extension points -------------------------------------------------

    def _authed_indicators(self) -> tuple[str, ...]:
        return (
            "a:has-text('Sign Out')",
            "button:has-text('Sign Out')",
            "a:has-text('Sign out')",
            "a[href*='signout']",
            "a[href*='sign-out']",
            "a[href*='logout']",
        )

    def _download_link_selectors(self) -> tuple[str, ...]:
        return (
            "a:has-text('Download')",
            "button:has-text('Download')",
            "a[aria-label*='Download']",
        )

    def _submit_button_selectors(self) -> tuple[str, ...]:
        return (
            "button:has-text('Download')",
            "button[type='submit']:has-text('Download')",
            "input[type='submit'][value*='Download']",
            "button[type='submit']",
            "input[type='submit']",
        )

    def _configure_download_form(self, page: Page) -> None:
        """Hook for selecting CSV / current period / etc. before submitting.

        Default picks "CSV" from any visible file-type ``<select>`` so most
        banks land on a sensible default. Per-bank subclasses override for
        site-specific dropdowns.
        """

        file_type = first_visible(
            page,
            (
                "select[name='fileType']",
                "select[name='filetype']",
                "select#fileFormat",
                "select#filetype",
                "select[name='downloadType']",
                "select[name='format']",
            ),
        )
        if file_type is None:
            return
        for value, label in (
            ("CSV", None),
            ("csv", None),
            (None, "Comma Separated Values (.csv)"),
            (None, "Spreadsheet (CSV)"),
            (None, "Microsoft Excel Format"),
            (None, "Microsoft Excel (.csv)"),
        ):
            try:
                if value:
                    file_type.select_option(value=value)
                else:
                    file_type.select_option(label=label)
                return
            except Exception:
                continue


class ChaseAccountAdapter(_BaseAccountAdapter):
    """Chase: each account has its own ``aId``-based activity URL."""

    LOGIN_URL_FRAGMENTS = ("logon", "signin", "auth/login")

    def _authed_indicators(self) -> tuple[str, ...]:
        return (
            "[data-testid='dashboardTile']",
            "button:has-text('Sign out')",
            "mds-text:has-text('Accounts')",
            "a:has-text('Account activity')",
        )

    def _download_link_selectors(self) -> tuple[str, ...]:
        return (
            "a:has-text('Download account activity')",
            "a:has-text('Download')",
            "button:has-text('Download')",
        )

    def _submit_button_selectors(self) -> tuple[str, ...]:
        return (
            "button[data-testid='download-submit']",
            "button:has-text('Download'):not(:has-text('Download account'))",
            "button[type='submit']:has-text('Download')",
            "input[type='submit'][value*='Download']",
        )


class MarcusAccountAdapter(_BaseAccountAdapter):
    """Marcus by Goldman: post-login activity pages are per-account."""

    LOGIN_URL_FRAGMENTS = ("login", "signin")

    def _authed_indicators(self) -> tuple[str, ...]:
        return (
            "a:has-text('Sign Out')",
            "[data-test='primary-nav']",
            "header:has-text('Accounts')",
        )

    def _download_link_selectors(self) -> tuple[str, ...]:
        return (
            "a:has-text('Download transactions')",
            "a:has-text('Download')",
            "button:has-text('Download')",
        )


class AmexAccountAdapter(_BaseAccountAdapter):
    """American Express card activity export."""

    LOGIN_URL_FRAGMENTS = ("logon", "login", "signon")

    def _authed_indicators(self) -> tuple[str, ...]:
        return (
            "a:has-text('Log Out')",
            "a:has-text('Sign Out')",
            "[data-module-name='HomepageHero']",
            "section[aria-label*='Account']",
        )

    def _download_link_selectors(self) -> tuple[str, ...]:
        return (
            "a:has-text('Download Transactions')",
            "a:has-text('Download')",
            "button:has-text('Download')",
        )

    def _submit_button_selectors(self) -> tuple[str, ...]:
        return (
            "button:has-text('Download')",
            "button[data-testid*='download']",
            "button[type='submit']:has-text('Download')",
        )


class FidelityAccountAdapter(_BaseAccountAdapter):
    """Fidelity activity export."""

    LOGIN_URL_FRAGMENTS = ("login", "signin", "ftgw")

    def _authed_indicators(self) -> tuple[str, ...]:
        return (
            "a:has-text('Log Out')",
            "a:has-text('Sign Out')",
            "[id*='accountSummary']",
            "header:has-text('Accounts')",
        )

    def _download_link_selectors(self) -> tuple[str, ...]:
        return (
            "a:has-text('Download')",
            "button:has-text('Download')",
            "a[aria-label*='Download']",
        )


_ADAPTERS = {
    "bofa": BofaAccountAdapter,
    "chase": ChaseAccountAdapter,
    "marcus": MarcusAccountAdapter,
    "amex": AmexAccountAdapter,
    "fidelity": FidelityAccountAdapter,
}


def get_account_adapter(institution_slug: str, account: AutomationAccount):
    """Resolve a per-account adapter for ``institution_slug``.

    Raises :class:`DomBroken` for unknown slugs so the runner can record a
    structured failure rather than crashing on a ``KeyError``.
    """

    adapter_cls = _ADAPTERS.get(institution_slug)
    if adapter_cls is None:
        raise DomBroken(
            f"No multi-account adapter for institution {institution_slug!r}"
        )
    return adapter_cls(account)
