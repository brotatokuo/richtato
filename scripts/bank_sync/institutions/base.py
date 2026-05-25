"""Base institution adapter contract for the bank-sync agent."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, Page


@dataclass
class DiscoveredAccount:
    """One bank-side account surfaced after a successful interactive login."""

    detected_account_name: str
    activity_url: str = ""
    external_account_token: str = ""
    flow: str = "deposit"

    def as_payload(self) -> dict[str, Any]:
        return {
            "detected_account_name": self.detected_account_name,
            "activity_url": self.activity_url,
            "external_account_token": self.external_account_token,
            "flow": self.flow,
        }


class BaseInstitutionAdapter:
    """Subclass per institution. All methods are async."""

    #: Override per subclass.
    slug: str = ""
    institution_display_name: str = ""
    login_url: str = ""
    post_login_url_substrings: tuple[str, ...] = ()

    async def interactive_login(
        self,
        context: BrowserContext,
        page: Page,
    ) -> list[DiscoveredAccount]:
        """Drive the headed sign-in flow and return discovered accounts.

        Implementations should:

        1. Navigate ``page`` to ``self.login_url``.
        2. Wait for ``self.post_login_url_substrings`` to appear in the URL
           (i.e. the user finished the sign-in/MFA flow).
        3. Optionally crawl ``page`` to extract account names, tokens, and
           activity URLs into a list of :class:`DiscoveredAccount`.

        Returning an empty list is fine — the user can paste activity URLs
        from the Connect-bank wizard if discovery misses an account.
        """

        raise NotImplementedError

    async def download_account(
        self,
        page: Page,
        *,
        activity_url: str,
        flow: str,
        download_dir: Path,
    ) -> Path:
        """Navigate to ``activity_url`` and download one statement file.

        Returns the local file path. Raises
        :class:`scripts.bank_sync.errors.NeedsReauthError` if the page
        redirects to a sign-in screen and
        :class:`scripts.bank_sync.errors.NoDownloadError` if the bank
        produced no file.
        """

        raise NotImplementedError

    async def fetch_account_balance(
        self,
        page: Page,
        *,
        activity_url: str,
    ) -> Decimal:
        """Navigate to ``activity_url`` and scrape the current account balance.

        Used by investment-only institutions that expose balances on a
        dashboard page rather than downloadable statements. Raises
        :class:`scripts.bank_sync.errors.NeedsReauthError` when cookies
        expired and :class:`scripts.bank_sync.errors.NoDownloadError` when
        the balance element cannot be found.
        """

        raise NotImplementedError
