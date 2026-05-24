"""Google Drive storage backend for statement files."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import BinaryIO

from apps.financial_account.services.google_drive_service import GoogleDriveService
from apps.financial_account.storage.base import StoredFile


class GoogleDriveStatementStorage:
    """Read/write flat statement files in a Drive account folder."""

    def __init__(self):
        self.drive = GoogleDriveService()

    def list_files(self, uri: str) -> Iterable[StoredFile]:
        folder_id = self.drive.folder_id_from_uri(uri)
        connection = self.drive.connection_for_folder(folder_id)
        out: list[StoredFile] = []
        for file_metadata in self.drive.list_files(connection, folder_id):
            out.append(
                StoredFile(
                    relative_path=file_metadata.name,
                    absolute_uri=f"gdrive://{folder_id}/{file_metadata.name}",
                    size_bytes=file_metadata.size,
                    modified_at=self._modified_at(file_metadata.modified_time),
                    filename=file_metadata.name,
                    external_file_id=file_metadata.id,
                )
            )
        return out

    def open_file(self, uri: str, relative_path: str) -> BinaryIO:
        folder_id = self.drive.folder_id_from_uri(uri)
        connection = self.drive.connection_for_folder(folder_id)
        filename = self.drive.filename_from_relative_path(relative_path)
        file_id = self.drive.file_id_for_name(connection, folder_id, filename)
        return self.drive.download_file(connection, file_id)

    def file_hash(self, uri: str, relative_path: str) -> str:
        import hashlib

        with self.open_file(uri, relative_path) as handle:
            return hashlib.sha256(handle.read()).hexdigest()

    def write_file(self, uri: str, relative_path: str, content: bytes) -> StoredFile:
        folder_id = self.drive.folder_id_from_uri(uri)
        connection = self.drive.connection_for_folder(folder_id)
        filename = self.drive.filename_from_relative_path(relative_path)
        uploaded = self.drive.upload_file(connection, folder_id=folder_id, name=filename, content=content)
        return StoredFile(
            relative_path=filename,
            absolute_uri=f"gdrive://{folder_id}/{filename}",
            size_bytes=uploaded.size or len(content),
            modified_at=self._modified_at(uploaded.modified_time),
            filename=filename,
            external_file_id=uploaded.id,
        )

    def delete_file(self, uri: str, relative_path: str) -> None:
        folder_id = self.drive.folder_id_from_uri(uri)
        connection = self.drive.connection_for_folder(folder_id)
        filename = self.drive.filename_from_relative_path(relative_path)
        try:
            file_id = self.drive.file_id_for_name(connection, folder_id, filename)
        except FileNotFoundError:
            return
        self.drive.delete_file(connection, file_id)

    def move_file(self, uri: str, old_relative_path: str, new_relative_path: str) -> None:
        folder_id = self.drive.folder_id_from_uri(uri)
        connection = self.drive.connection_for_folder(folder_id)
        old_name = self.drive.filename_from_relative_path(old_relative_path)
        new_name = self.drive.filename_from_relative_path(new_relative_path)
        if old_name == new_name:
            return
        file_id = self.drive.file_id_for_name(connection, folder_id, old_name)
        self.drive.rename_file(connection, file_id, new_name)

    def _modified_at(self, value: str) -> float:
        if not value:
            return 0.0
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0
