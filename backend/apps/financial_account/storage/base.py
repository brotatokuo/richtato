"""Storage interface shared by all statement-file backends."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import BinaryIO, Protocol


class UnknownStorageScheme(ValueError):
    """Raised when a storage URI scheme has no registered backend."""


@dataclass(frozen=True)
class StoredFile:
    """Metadata for a file discovered in a statement storage backend.

    ``relative_path`` is the storage-backend-relative path used as the
    canonical identifier (e.g. ``2026/05/abc12345-statement.csv``).
    ``absolute_uri`` is a fully-qualified URI suitable for logs and
    user-facing copy.
    """

    relative_path: str
    absolute_uri: str
    size_bytes: int
    modified_at: float
    filename: str


class StatementStorage(Protocol):
    """Read/write surface for one account's statement files."""

    def list_files(self, uri: str) -> Iterable[StoredFile]:
        """Enumerate files under ``uri``. Subdirectories are walked recursively."""

    def open_file(self, uri: str, relative_path: str) -> BinaryIO:
        """Open a file by storage-relative path; caller closes the handle."""

    def file_hash(self, uri: str, relative_path: str) -> str:
        """Return a sha256 hex digest of the file's bytes (idempotent)."""

    def write_file(
        self,
        uri: str,
        relative_path: str,
        content: bytes,
    ) -> StoredFile:
        """Persist ``content`` at ``relative_path`` under ``uri`` and return its metadata."""

    def delete_file(self, uri: str, relative_path: str) -> None:
        """Remove a file from storage. Should be a no-op if absent."""

    def move_file(
        self,
        uri: str,
        old_relative_path: str,
        new_relative_path: str,
    ) -> None:
        """Rename ``old_relative_path`` to ``new_relative_path`` within ``uri``."""
