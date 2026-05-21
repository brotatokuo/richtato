"""Typed failure kinds used by the automation pipeline.

Centralised so the runner, notifier, and state tracker agree on a small set of
known error categories. Anything unexpected becomes :class:`AutomationError`
with kind ``UNKNOWN``.
"""

from __future__ import annotations

from enum import Enum


class ErrorKind(str, Enum):
    SESSION_EXPIRED = "session_expired"
    DOM_BROKEN = "dom_broken"
    NO_DOWNLOAD = "no_download"
    IMPORT_REJECTED = "import_rejected"
    CONFIG = "config"
    UNKNOWN = "unknown"


class AutomationError(Exception):
    """Wraps a failure with a known :class:`ErrorKind` for notification routing."""

    def __init__(self, kind: ErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


class SessionExpired(AutomationError):
    def __init__(self, message: str = "Bank session expired") -> None:
        super().__init__(ErrorKind.SESSION_EXPIRED, message)


class DomBroken(AutomationError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorKind.DOM_BROKEN, message)


class NoDownload(AutomationError):
    def __init__(self, message: str = "Download never fired") -> None:
        super().__init__(ErrorKind.NO_DOWNLOAD, message)


class ImportRejected(AutomationError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorKind.IMPORT_REJECTED, message)


class ConfigError(AutomationError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorKind.CONFIG, message)
