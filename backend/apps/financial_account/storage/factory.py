"""Storage backend dispatch based on URI scheme."""

from __future__ import annotations

from urllib.parse import urlparse

from apps.financial_account.storage.base import StatementStorage, UnknownStorageScheme
from apps.financial_account.storage.gdrive import GoogleDriveStatementStorage


def get_storage(uri: str) -> StatementStorage:
    """Resolve a ``StatementStorage`` for the given URI scheme.

    Only ``gdrive://`` is supported for statement files.
    """
    if not uri:
        raise ValueError("Storage URI must not be empty")

    scheme = urlparse(uri).scheme
    if scheme == "gdrive":
        return GoogleDriveStatementStorage()

    raise UnknownStorageScheme(f"No storage backend registered for scheme: {scheme!r} (uri={uri!r})")
