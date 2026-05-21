"""Abstract base class for per-institution download adapters.

A concrete adapter only needs to declare ``URL`` (the page to land on after
loading the saved session) and the three navigation methods. The runner owns
the browser lifecycle and download capture - adapters just drive the page.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from playwright.sync_api import Download, Page

DEFAULT_NAV_TIMEOUT_MS = 30_000
DEFAULT_DOWNLOAD_TIMEOUT_MS = 90_000


class InstitutionAdapter(ABC):
    """Encapsulates the bank-specific navigation logic.

    Subclasses set ``SLUG`` matching the institution key and ``URL`` matching
    the post-login landing page where session validity can be inspected.
    """

    SLUG: str = ""
    URL: str = ""
    nav_timeout_ms: int = DEFAULT_NAV_TIMEOUT_MS
    download_timeout_ms: int = DEFAULT_DOWNLOAD_TIMEOUT_MS

    @abstractmethod
    def is_session_valid(self, page: Page) -> bool:
        """Return True when the page indicates an authenticated session.

        Implementations should check for an unambiguous post-login element
        (account summary, sign-out button, etc.) rather than relying on URL
        comparisons, which can be flaky across A/B splits.
        """

    @abstractmethod
    def navigate_to_export(self, page: Page) -> None:
        """Click through to the page that contains the CSV/XLSX export control.

        Raise :class:`scripts.automation.errors.SessionExpired` if the bank
        redirects to a login screen at any point. Raise
        :class:`scripts.automation.errors.DomBroken` if a selector is missing.
        """

    @abstractmethod
    def trigger_download(self, page: Page) -> Download:
        """Click the export control and return the resulting Download.

        Implementations should wrap the click in ``page.expect_download`` and
        return the resolved download. Raise
        :class:`scripts.automation.errors.NoDownload` if no download fires
        within the configured timeout.
        """
