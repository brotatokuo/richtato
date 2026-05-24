"""Agent-side storage writer used to upload downloaded statement files."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

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
    """Upload ``content`` to the account's Google Drive folder through Richtato."""
    if not storage_uri.startswith("gdrive://"):
        raise ValueError(
            f"Unsupported storage URI: {storage_uri!r}. Configure Google Drive statement storage first."
        )
    if not (1 <= month <= 12):
        raise ValueError(f"month must be between 1 and 12, got {month}")
    if not filename:
        raise ValueError("filename must not be empty")

    safe_name = _sanitize_filename(filename)
    file_hash = hashlib.sha256(content).hexdigest()
    return _write_statement_to_backend(
        storage_uri,
        year=year,
        month=month,
        filename=safe_name,
        content=content,
        file_hash=file_hash,
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
        raise ValueError("RICHTATO_API_TOKEN is required for Google Drive statement uploads.")

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


def _sanitize_filename(filename: str) -> str:
    """Match the backend's ``get_valid_filename`` behavior closely enough."""
    cleaned = []
    for char in filename.strip():
        if char in {" ", "\t", "\n"}:
            cleaned.append("_")
        elif char.isalnum() or char in {".", "_", "-"}:
            cleaned.append(char)
    result = "".join(cleaned)
    return result or "statement.csv"
