"""Pluggable storage backends for statement files.

Statement files are stored in Google Drive. Resolve a backend with
:func:`get_storage` using a ``gdrive://<folder_id>`` URI.
"""

from apps.financial_account.storage.base import (
    StatementStorage,
    StoredFile,
    UnknownStorageScheme,
)
from apps.financial_account.storage.factory import get_storage
from apps.financial_account.storage.gdrive import GoogleDriveStatementStorage

__all__ = [
    "GoogleDriveStatementStorage",
    "StatementStorage",
    "StoredFile",
    "UnknownStorageScheme",
    "get_storage",
]
