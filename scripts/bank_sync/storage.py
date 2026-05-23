"""Agent-side storage writer used to deposit downloaded statement files.

Mirrors the backend's ``apps.financial_account.storage`` interface but
intentionally minimal: the agent only ever writes files, never reads or
deletes them. The Richtato app owns discovery and import via its own
storage backends.

Today only ``file://`` URIs are supported. ``gdrive://`` will land here
later as a second backend (alongside its backend-side counterpart).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


@dataclass(frozen=True)
class WrittenFile:
    """Result of writing one downloaded statement file."""

    absolute_path: Path
    relative_path: str
    size_bytes: int
    sha256: str


def write_statement(
    storage_uri: str,
    *,
    year: int,
    month: int,
    filename: str,
    content: bytes,
) -> WrittenFile:
    """Write ``content`` into the account's storage URI.

    Uses the same ``<year>/<month>/<hash12>-<filename>`` layout the backend
    scanner expects, so the import side picks the file up automatically.
    """
    if not (1 <= month <= 12):
        raise ValueError(f"month must be between 1 and 12, got {month}")
    if not filename:
        raise ValueError("filename must not be empty")

    safe_name = _sanitize_filename(filename)
    file_hash = hashlib.sha256(content).hexdigest()
    relative = f"{year}/{month:02d}/{file_hash[:12]}-{safe_name}"
    root = _uri_to_path(storage_uri)
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return WrittenFile(
        absolute_path=target,
        relative_path=relative,
        size_bytes=len(content),
        sha256=file_hash,
    )


def _uri_to_path(uri: str) -> Path:
    """Resolve a ``file://`` URI (or bare absolute path) to a ``Path``."""
    if not uri:
        raise ValueError("storage_uri must not be empty")
    if uri.startswith("file://"):
        parsed = urlparse(uri)
        return Path(unquote(parsed.path))
    if uri.startswith("/"):
        return Path(uri)
    raise ValueError(
        f"Unsupported storage URI scheme: {uri!r}. Only file:// and bare absolute paths are supported on the agent."
    )


def _sanitize_filename(filename: str) -> str:
    """Match the backend's ``get_valid_filename`` behavior closely enough.

    Replaces whitespace with underscores and drops characters that would
    create cross-OS issues. The exact mapping is not critical — the file
    hash prefix already disambiguates collisions.
    """
    cleaned = []
    for char in filename.strip():
        if char in {" ", "\t", "\n"}:
            cleaned.append("_")
        elif char.isalnum() or char in {".", "_", "-"}:
            cleaned.append(char)
    result = "".join(cleaned)
    return result or "statement.csv"
