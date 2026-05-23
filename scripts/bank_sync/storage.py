"""Agent-side storage writer used to deposit downloaded statement files."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests


@dataclass(frozen=True)
class WrittenFile:
    """Result of writing one downloaded statement file."""

    absolute_path: Path | str
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

    Local ``file://`` storage uses ``<year>/<month>/<hash12>-<filename>``.
    Drive-backed storage is uploaded through Richtato so the backend can use
    the user's stored Google OAuth token and import the statement immediately.
    """
    if not (1 <= month <= 12):
        raise ValueError(f"month must be between 1 and 12, got {month}")
    if not filename:
        raise ValueError("filename must not be empty")

    safe_name = _sanitize_filename(filename)
    file_hash = hashlib.sha256(content).hexdigest()
    if storage_uri.startswith("gdrive://"):
        return _write_statement_to_backend(
            storage_uri,
            year=year,
            month=month,
            filename=safe_name,
            content=content,
            file_hash=file_hash,
        )

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


def _write_statement_to_backend(
    storage_uri: str,
    *,
    year: int,
    month: int,
    filename: str,
    content: bytes,
    file_hash: str,
) -> WrittenFile:
    api_base = os.environ.get("RICHTATO_API_BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
    token = os.environ.get("RICHTATO_API_TOKEN", "")
    if not token:
        raise ValueError("RICHTATO_API_TOKEN is required for gdrive:// statement uploads.")

    response = requests.post(
        f"{api_base}/accounts/agent-statements/",
        headers={"Authorization": f"Token {token}"},
        data={
            "storage_uri": storage_uri,
            "statement_year": str(year),
            "statement_month": str(month),
            "statement_period": f"{year}-{month:02d}",
        },
        files={"file": (filename, content, "application/octet-stream")},
        timeout=60,
    )
    if not response.ok:
        raise ValueError(f"Richtato agent statement upload failed: HTTP {response.status_code} {response.text[:500]}")
    payload = response.json()
    statement = payload.get("statement", {})
    stored_path = statement.get("stored_path") or f"{storage_uri.rstrip('/')}/{file_hash[:12]}-{filename}"
    return WrittenFile(
        absolute_path=stored_path,
        relative_path=Path(stored_path).name,
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
        f"Unsupported storage URI scheme: {uri!r}. Supported schemes are file:// and gdrive://."
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
