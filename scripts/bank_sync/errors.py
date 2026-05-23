"""Custom exceptions raised by the bank-sync agent and adapters."""

from __future__ import annotations


class AgentError(Exception):
    """Base class for bank-sync agent errors."""


class NeedsReauthError(AgentError):
    """Raised when the stored storage_state no longer authenticates."""


class LoginCancelledError(AgentError):
    """Raised when the user closes the headed browser without completing login."""


class DomBrokenError(AgentError):
    """Raised when the bank DOM no longer matches the adapter's expectations."""


class NoDownloadError(AgentError):
    """Raised when no statement file was produced for a given account."""


class ImportRejectedError(AgentError):
    """Raised when Richtato's /import-statement/ endpoint rejected the file."""
