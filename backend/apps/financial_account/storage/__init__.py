"""Pluggable storage backends for statement files.

The agent (host process) and the backend (Django app) both read and write
statements through this abstraction. Today only ``file://`` (local
filesystem) is implemented; ``gdrive://`` is reserved as a future option.

Resolve a backend with :func:`get_storage`. Backends should be cheap to
instantiate so the scanner can build them per-account in a loop.
"""

from apps.financial_account.storage.base import (
    StatementStorage,
    StoredFile,
    UnknownStorageScheme,
)
from apps.financial_account.storage.factory import get_storage
from apps.financial_account.storage.gdrive import GoogleDriveStatementStorage
from apps.financial_account.storage.local import LocalStatementStorage

__all__ = [
    "GoogleDriveStatementStorage",
    "LocalStatementStorage",
    "StatementStorage",
    "StoredFile",
    "UnknownStorageScheme",
    "get_storage",
]
