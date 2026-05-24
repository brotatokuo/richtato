"""In-memory Google Drive storage for tests."""

from __future__ import annotations

import hashlib
import io
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from apps.financial_account.storage.base import StoredFile

SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}


@dataclass
class FakeGoogleDriveStorage:
    """Minimal flat-folder storage keyed by ``gdrive://`` folder id."""

    files_by_folder: dict[str, dict[str, bytes]] = field(default_factory=dict)

    def list_files(self, uri: str) -> Iterable[StoredFile]:
        folder_id = _folder_id_from_uri(uri)
        out: list[StoredFile] = []
        for filename, content in sorted(self.files_by_folder.get(folder_id, {}).items()):
            if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            out.append(
                StoredFile(
                    relative_path=filename,
                    absolute_uri=f"gdrive://{folder_id}/{filename}",
                    size_bytes=len(content),
                    modified_at=0.0,
                    filename=filename,
                )
            )
        return out

    def open_file(self, uri: str, relative_path: str) -> io.BytesIO:
        folder_id = _folder_id_from_uri(uri)
        filename = Path(relative_path).name
        try:
            return io.BytesIO(self.files_by_folder[folder_id][filename])
        except KeyError as exc:
            raise FileNotFoundError(filename) from exc

    def file_hash(self, uri: str, relative_path: str) -> str:
        with self.open_file(uri, relative_path) as handle:
            return hashlib.sha256(handle.read()).hexdigest()

    def write_file(self, uri: str, relative_path: str, content: bytes) -> StoredFile:
        folder_id = _folder_id_from_uri(uri)
        filename = Path(relative_path).name
        self.files_by_folder.setdefault(folder_id, {})[filename] = content
        return StoredFile(
            relative_path=filename,
            absolute_uri=f"gdrive://{folder_id}/{filename}",
            size_bytes=len(content),
            modified_at=0.0,
            filename=filename,
            external_file_id=f"fake-file-{folder_id}-{filename}",
        )

    def delete_file(self, uri: str, relative_path: str) -> None:
        folder_id = _folder_id_from_uri(uri)
        filename = Path(relative_path).name
        self.files_by_folder.get(folder_id, {}).pop(filename, None)

    def move_file(self, uri: str, old_relative_path: str, new_relative_path: str) -> None:
        folder_id = _folder_id_from_uri(uri)
        old_name = Path(old_relative_path).name
        new_name = Path(new_relative_path).name
        if old_name == new_name:
            return
        folder = self.files_by_folder.setdefault(folder_id, {})
        content = folder.pop(old_name)
        folder[new_name] = content


def _folder_id_from_uri(uri: str) -> str:
    parsed = urlparse(uri)
    folder_id = parsed.netloc or parsed.path.strip("/")
    if not folder_id:
        raise ValueError("gdrive:// URI must include a folder id.")
    return folder_id
