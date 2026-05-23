"""Google Drive storage backend stub.

Reserved for future migration: each ``FinancialAccount.storage_uri`` of the
form ``gdrive://<folder_id>`` will route here. The agent (host) and Django
both authenticate with the user's Drive OAuth credentials and exchange
statement files through that folder.

Implement the :class:`StatementStorage` protocol when you are ready to
wire Drive in; until then :func:`get_storage` raises
``NotImplementedError`` for ``gdrive://`` URIs.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import BinaryIO

from apps.financial_account.storage.base import StoredFile


class GoogleDriveStatementStorage:  # pragma: no cover - intentional stub
    """Placeholder for the future Drive backend."""

    def list_files(self, uri: str) -> Iterable[StoredFile]:
        raise NotImplementedError

    def open_file(self, uri: str, relative_path: str) -> BinaryIO:
        raise NotImplementedError

    def file_hash(self, uri: str, relative_path: str) -> str:
        raise NotImplementedError

    def write_file(self, uri: str, relative_path: str, content: bytes) -> StoredFile:
        raise NotImplementedError

    def delete_file(self, uri: str, relative_path: str) -> None:
        raise NotImplementedError

    def move_file(self, uri: str, old_relative_path: str, new_relative_path: str) -> None:
        raise NotImplementedError
