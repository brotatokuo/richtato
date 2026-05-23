"""Storage backend dispatch based on URI scheme."""

from __future__ import annotations

from urllib.parse import urlparse

from apps.financial_account.storage.base import StatementStorage, UnknownStorageScheme
from apps.financial_account.storage.gdrive import GoogleDriveStatementStorage
from apps.financial_account.storage.local import LocalStatementStorage


def get_storage(uri: str) -> StatementStorage:
    """Resolve a ``StatementStorage`` for the given URI scheme.

    ``file://`` and bare absolute paths route to :class:`LocalStatementStorage`.
    ``gdrive://`` routes to :class:`GoogleDriveStatementStorage`.
    Unknown schemes raise :class:`UnknownStorageScheme`.
    """
    if not uri:
        raise ValueError("Storage URI must not be empty")

    if uri.startswith("/") or uri.startswith("file://"):
        return LocalStatementStorage()

    scheme = urlparse(uri).scheme
    if scheme == "gdrive":
        return GoogleDriveStatementStorage()

    raise UnknownStorageScheme(f"No storage backend registered for scheme: {scheme!r} (uri={uri!r})")
