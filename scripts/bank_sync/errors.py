"""Custom exceptions raised by the bank-sync agent and adapters."""

from __future__ import annotations

from enum import StrEnum


class FailureKind(StrEnum):
    """Structured failure categories aligned with legacy Django bank_sync models."""

    NEEDS_REAUTH = "needs_reauth"
    DOM_BROKEN = "dom_broken"
    NO_DOWNLOAD = "no_download"
    IMPORT_REJECTED = "import_rejected"
    LOGIN_CANCELLED = "login_cancelled"
    CONFIG = "config"
    UNKNOWN = "unknown"


# Lower number = higher severity when aggregating multi-account failures.
FAILURE_KIND_PRIORITY: dict[FailureKind, int] = {
    FailureKind.NEEDS_REAUTH: 0,
    FailureKind.DOM_BROKEN: 1,
    FailureKind.IMPORT_REJECTED: 2,
    FailureKind.NO_DOWNLOAD: 3,
    FailureKind.LOGIN_CANCELLED: 4,
    FailureKind.CONFIG: 5,
    FailureKind.UNKNOWN: 6,
}


def format_failure_reason(kind: FailureKind, message: str) -> str:
    """Build a machine-readable failure string for vault storage."""
    return f"[{kind}] {message}"


def parse_failure_kind(text: str) -> FailureKind | None:
    """Extract a :class:`FailureKind` from a prefixed failure string."""
    if not text.startswith("[") or "]" not in text:
        return None
    candidate = text[1 : text.index("]")]
    try:
        return FailureKind(candidate)
    except ValueError:
        return None


def strip_failure_prefix(text: str) -> str:
    """Remove a leading ``[kind]`` prefix from a stored failure string."""
    kind = parse_failure_kind(text)
    if kind is None:
        return text
    prefix = f"[{kind}]"
    if text.startswith(prefix):
        return text[len(prefix) :].lstrip()
    return text


def worst_failure_kind(kinds: list[FailureKind]) -> FailureKind | None:
    """Return the most severe failure kind from ``kinds``."""
    if not kinds:
        return None
    return min(kinds, key=lambda kind: FAILURE_KIND_PRIORITY[kind])


class AgentError(Exception):
    """Base class for bank-sync agent errors."""

    kind: FailureKind = FailureKind.UNKNOWN

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message


class NeedsReauthError(AgentError):
    """Raised when the stored storage_state no longer authenticates."""

    kind = FailureKind.NEEDS_REAUTH


class LoginCancelledError(AgentError):
    """Raised when the user closes the headed browser without completing login."""

    kind = FailureKind.LOGIN_CANCELLED


class DomBrokenError(AgentError):
    """Raised when the bank DOM no longer matches the adapter's expectations."""

    kind = FailureKind.DOM_BROKEN


class NoDownloadError(AgentError):
    """Raised when no statement file was produced for a given account."""

    kind = FailureKind.NO_DOWNLOAD


class ImportRejectedError(AgentError):
    """Raised when Richtato's upload endpoint rejected the file or balance."""

    kind = FailureKind.IMPORT_REJECTED


def failure_kind_for(exc: BaseException) -> FailureKind:
    """Map an exception to a :class:`FailureKind`."""
    if isinstance(exc, AgentError):
        return exc.kind
    return FailureKind.UNKNOWN
