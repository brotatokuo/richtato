"""Local-filesystem storage backend for statement files."""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import BinaryIO
from urllib.parse import unquote, urlparse

from apps.financial_account.storage.base import StoredFile

SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}


class LocalStatementStorage:
    """Read/write statement files on the local filesystem.

    Accepts ``file://`` URIs (with or without a host segment) and bare
    absolute paths. ``relative_path`` arguments are joined onto the URI's
    resolved directory; absolute relative paths are rejected to prevent
    escape.
    """

    def list_files(self, uri: str) -> Iterable[StoredFile]:
        root = self._uri_to_path(uri)
        if not root.exists():
            return []
        out: list[StoredFile] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            stat = path.stat()
            rel = path.relative_to(root).as_posix()
            out.append(
                StoredFile(
                    relative_path=rel,
                    absolute_uri=f"file://{path}",
                    size_bytes=stat.st_size,
                    modified_at=stat.st_mtime,
                    filename=path.name,
                )
            )
        return out

    def open_file(self, uri: str, relative_path: str) -> BinaryIO:
        return self._resolve_relative(uri, relative_path).open("rb")

    def file_hash(self, uri: str, relative_path: str) -> str:
        path = self._resolve_relative(uri, relative_path)
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def write_file(self, uri: str, relative_path: str, content: bytes) -> StoredFile:
        target = self._resolve_relative(uri, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        stat = target.stat()
        return StoredFile(
            relative_path=Path(relative_path).as_posix(),
            absolute_uri=f"file://{target}",
            size_bytes=stat.st_size,
            modified_at=stat.st_mtime,
            filename=target.name,
        )

    def delete_file(self, uri: str, relative_path: str) -> None:
        target = self._resolve_relative(uri, relative_path)
        if target.exists():
            target.unlink()

    def move_file(self, uri: str, old_relative_path: str, new_relative_path: str) -> None:
        old = self._resolve_relative(uri, old_relative_path)
        new = self._resolve_relative(uri, new_relative_path)
        if old == new:
            return
        new.parent.mkdir(parents=True, exist_ok=True)
        if old.exists():
            shutil.move(str(old), str(new))

    def _uri_to_path(self, uri: str) -> Path:
        """Convert a ``file://`` URI (or bare path) to an absolute ``Path``."""
        if not uri:
            raise ValueError("Local storage URI must not be empty")
        if uri.startswith("file://"):
            parsed = urlparse(uri)
            # ``file:///abs/path`` -> netloc="", path="/abs/path"
            # ``file://host/abs/path`` -> netloc="host" (ignore host segment)
            return Path(unquote(parsed.path))
        return Path(uri)

    def _resolve_relative(self, uri: str, relative_path: str) -> Path:
        rel = Path(relative_path)
        if rel.is_absolute():
            raise ValueError(f"relative_path must be relative, got: {relative_path}")
        return self._uri_to_path(uri) / rel
