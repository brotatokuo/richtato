"""Google Drive OAuth and file operations for statement storage."""

from __future__ import annotations

import io
import json
import mimetypes
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

import requests
from django.conf import settings
from django.utils import timezone
from django.utils.text import get_valid_filename

from apps.financial_account.models import FinancialAccount, GoogleDriveAccountFolder, GoogleDriveConnection
from apps.richtato_user.models import User

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
GOOGLE_DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
DRIVE_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
DRIVE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleDriveError(ValueError):
    """Raised when Drive OAuth or file operations fail."""


@dataclass(frozen=True)
class DriveFileMetadata:
    """Small Drive file shape used by storage backends."""

    id: str
    name: str
    size: int
    modified_time: str
    mime_type: str


class GoogleDriveService:
    """Thin requests-based wrapper around OAuth and Drive APIs."""

    def build_authorization_url(self, request, *, state: str | None = None) -> tuple[str, str]:
        self._require_oauth_settings()
        state = state or uuid.uuid4().hex
        redirect_uri = self._redirect_uri(request)
        params = {
            "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(DRIVE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "include_granted_scopes": "true",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}", state

    def exchange_code(self, *, user: User, code: str, request) -> GoogleDriveConnection:
        self._require_oauth_settings()
        token_payload = self._post_token(
            {
                "code": code,
                "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
                "client_secret": settings.GOOGLE_DRIVE_CLIENT_SECRET,
                "redirect_uri": self._redirect_uri(request),
                "grant_type": "authorization_code",
            }
        )
        refresh_token = token_payload.get("refresh_token")
        if not refresh_token:
            raise GoogleDriveError("Google did not return a refresh token. Reconnect and approve offline access.")

        userinfo = self._get_userinfo(token_payload["access_token"])
        connection, _ = GoogleDriveConnection.objects.get_or_create(user=user)
        connection.google_account_email = userinfo.get("email", "")
        connection.set_refresh_token(refresh_token)
        connection.connected_at = timezone.now()
        connection.disconnected_at = None
        connection.last_error = ""
        connection.save(
            update_fields=[
                "google_account_email",
                "refresh_token_encrypted",
                "connected_at",
                "disconnected_at",
                "last_error",
                "updated_at",
            ]
        )
        return connection

    def get_picker_token(self, connection: GoogleDriveConnection) -> dict[str, str]:
        access_token = self.refresh_access_token(connection)
        return {
            "access_token": access_token,
            "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
            "developer_key": settings.GOOGLE_DRIVE_PICKER_API_KEY,
            "app_id": settings.GOOGLE_DRIVE_PICKER_APP_ID,
        }

    def refresh_access_token(self, connection: GoogleDriveConnection) -> str:
        self._require_oauth_settings()
        if not connection.refresh_token:
            raise GoogleDriveError("Google Drive is not connected.")
        payload = self._post_token(
            {
                "client_id": settings.GOOGLE_DRIVE_CLIENT_ID,
                "client_secret": settings.GOOGLE_DRIVE_CLIENT_SECRET,
                "refresh_token": connection.refresh_token,
                "grant_type": "refresh_token",
            }
        )
        return payload["access_token"]

    def validate_empty_folder(self, connection: GoogleDriveConnection, folder_id: str) -> DriveFileMetadata:
        folder = self.get_file(connection, folder_id, fields="id,name,mimeType,modifiedTime")
        if folder.mime_type != DRIVE_FOLDER_MIME_TYPE:
            raise GoogleDriveError("Selected Drive item must be a folder.")
        if self.list_files(connection, folder_id, include_folders=True):
            raise GoogleDriveError("Selected Drive folder must be empty.")
        return folder

    def get_file(
        self, connection: GoogleDriveConnection, file_id: str, *, fields: str | None = None
    ) -> DriveFileMetadata:
        access_token = self.refresh_access_token(connection)
        response = requests.get(
            f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
            headers=self._auth_headers(access_token),
            params={"fields": fields or "id,name,mimeType,size,modifiedTime"},
            timeout=20,
        )
        data = self._json_response(response)
        return self._metadata_from_response(data)

    def list_files(
        self,
        connection: GoogleDriveConnection,
        folder_id: str,
        *,
        include_folders: bool = False,
    ) -> list[DriveFileMetadata]:
        access_token = self.refresh_access_token(connection)
        q = f"'{self._escape_query(folder_id)}' in parents and trashed = false"
        if not include_folders:
            q += f" and mimeType != '{DRIVE_FOLDER_MIME_TYPE}'"
        response = requests.get(
            GOOGLE_DRIVE_FILES_URL,
            headers=self._auth_headers(access_token),
            params={
                "q": q,
                "fields": "files(id,name,mimeType,size,modifiedTime)",
                "pageSize": 1000,
            },
            timeout=20,
        )
        data = self._json_response(response)
        return [self._metadata_from_response(item) for item in data.get("files", [])]

    def create_folder(self, connection: GoogleDriveConnection, *, parent_id: str, name: str) -> DriveFileMetadata:
        access_token = self.refresh_access_token(connection)
        response = requests.post(
            GOOGLE_DRIVE_FILES_URL,
            headers={**self._auth_headers(access_token), "Content-Type": "application/json"},
            data=json.dumps(
                {
                    "name": name,
                    "mimeType": DRIVE_FOLDER_MIME_TYPE,
                    "parents": [parent_id],
                }
            ),
            params={"fields": "id,name,mimeType,modifiedTime"},
            timeout=20,
        )
        return self._metadata_from_response(self._json_response(response))

    def upload_file(
        self,
        connection: GoogleDriveConnection,
        *,
        folder_id: str,
        name: str,
        content: bytes,
        content_type: str = "",
    ) -> DriveFileMetadata:
        access_token = self.refresh_access_token(connection)
        boundary = f"richtato-{uuid.uuid4().hex}"
        metadata = {"name": name, "parents": [folder_id]}
        media_type = content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
        body = (
            (
                f"--{boundary}\r\n"
                "Content-Type: application/json; charset=UTF-8\r\n\r\n"
                f"{json.dumps(metadata)}\r\n"
                f"--{boundary}\r\n"
                f"Content-Type: {media_type}\r\n\r\n"
            ).encode()
            + content
            + f"\r\n--{boundary}--\r\n".encode()
        )
        response = requests.post(
            GOOGLE_DRIVE_UPLOAD_URL,
            headers={
                **self._auth_headers(access_token),
                "Content-Type": f"multipart/related; boundary={boundary}",
            },
            params={"uploadType": "multipart", "fields": "id,name,mimeType,size,modifiedTime"},
            data=body,
            timeout=60,
        )
        return self._metadata_from_response(self._json_response(response))

    def download_file(self, connection: GoogleDriveConnection, file_id: str) -> io.BytesIO:
        access_token = self.refresh_access_token(connection)
        response = requests.get(
            f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
            headers=self._auth_headers(access_token),
            params={"alt": "media"},
            timeout=60,
        )
        if not response.ok:
            raise GoogleDriveError(self._error_message(response))
        return io.BytesIO(response.content)

    def delete_file(self, connection: GoogleDriveConnection, file_id: str) -> None:
        access_token = self.refresh_access_token(connection)
        response = requests.delete(
            f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
            headers=self._auth_headers(access_token),
            timeout=20,
        )
        if response.status_code not in {200, 204, 404}:
            raise GoogleDriveError(self._error_message(response))

    def rename_file(self, connection: GoogleDriveConnection, file_id: str, new_name: str) -> DriveFileMetadata:
        access_token = self.refresh_access_token(connection)
        response = requests.patch(
            f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
            headers={**self._auth_headers(access_token), "Content-Type": "application/json"},
            params={"fields": "id,name,mimeType,size,modifiedTime"},
            data=json.dumps({"name": new_name}),
            timeout=20,
        )
        return self._metadata_from_response(self._json_response(response))

    def connection_for_folder(self, folder_id: str) -> GoogleDriveConnection:
        account_folder = (
            GoogleDriveAccountFolder.objects.select_related("connection")
            .filter(folder_id=folder_id, connection__is_active=True)
            .first()
        )
        if not account_folder:
            raise GoogleDriveError("No active Google Drive connection owns this folder.")
        return account_folder.connection

    def account_folder_name(self, account: FinancialAccount) -> str:
        safe_name = get_valid_filename(account.name).strip("._-") or "account"
        return f"{account.id}-{safe_name}"

    def folder_id_from_uri(self, uri: str) -> str:
        parsed = urlparse(uri)
        folder_id = parsed.netloc or parsed.path.strip("/")
        if not folder_id:
            raise GoogleDriveError("gdrive:// URI must include a folder id.")
        return folder_id

    def filename_from_relative_path(self, relative_path: str) -> str:
        return Path(relative_path).name

    def file_id_for_name(self, connection: GoogleDriveConnection, folder_id: str, filename: str) -> str:
        matches = [item for item in self.list_files(connection, folder_id) if item.name == filename]
        if not matches:
            raise FileNotFoundError(filename)
        return matches[0].id

    def _post_token(self, data: dict[str, str]) -> dict[str, Any]:
        response = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=20)
        return self._json_response(response)

    def _get_userinfo(self, access_token: str) -> dict[str, Any]:
        response = requests.get(GOOGLE_USERINFO_URL, headers=self._auth_headers(access_token), timeout=20)
        return self._json_response(response)

    def _redirect_uri(self, request) -> str:
        configured = settings.GOOGLE_DRIVE_REDIRECT_URI
        if configured:
            return configured
        return request.build_absolute_uri("/api/v1/accounts/drive/oauth/callback/")

    def _require_oauth_settings(self) -> None:
        if not settings.GOOGLE_DRIVE_CLIENT_ID or not settings.GOOGLE_DRIVE_CLIENT_SECRET:
            raise GoogleDriveError("Google Drive OAuth is not configured.")

    def _auth_headers(self, access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    def _json_response(self, response: requests.Response) -> dict[str, Any]:
        if not response.ok:
            raise GoogleDriveError(self._error_message(response))
        try:
            return response.json()
        except ValueError as exc:
            raise GoogleDriveError("Google returned an invalid JSON response.") from exc

    def _metadata_from_response(self, data: dict[str, Any]) -> DriveFileMetadata:
        return DriveFileMetadata(
            id=data.get("id", ""),
            name=data.get("name", ""),
            size=int(data.get("size") or 0),
            modified_time=data.get("modifiedTime", ""),
            mime_type=data.get("mimeType", ""),
        )

    def _error_message(self, response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"Google Drive request failed: HTTP {response.status_code}"
        error = payload.get("error", {})
        if isinstance(error, dict):
            return error.get("message") or f"Google Drive request failed: HTTP {response.status_code}"
        if isinstance(error, str):
            return error
        return f"Google Drive request failed: HTTP {response.status_code}"

    def _escape_query(self, value: str) -> str:
        return re.sub(r"(['\\])", r"\\\1", value)
