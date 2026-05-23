"""Activate Google Drive as the canonical statement store."""

from __future__ import annotations

from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone
from loguru import logger

from apps.financial_account.models import (
    FinancialAccount,
    GoogleDriveAccountFolder,
    GoogleDriveConnection,
    StatementFile,
)
from apps.financial_account.services.google_drive_service import GoogleDriveError, GoogleDriveService
from apps.financial_account.services.statement_file_service import StatementFileService
from apps.financial_account.storage import get_storage
from apps.richtato_user.models import User


@dataclass
class DriveActivationResult:
    """Summary of a Drive activation/migration run."""

    connection: GoogleDriveConnection
    account_folders_created: int = 0
    statements_migrated: int = 0
    errors: list[str] = field(default_factory=list)


class GoogleDriveActivationService:
    """Create account folders, migrate tracked files, and switch accounts to Drive."""

    def __init__(self):
        self.drive = GoogleDriveService()
        self.statement_files = StatementFileService()

    def activate(self, user: User, *, root_folder_id: str, root_folder_name: str = "") -> DriveActivationResult:
        connection = GoogleDriveConnection.objects.filter(user=user).first()
        if not connection:
            raise GoogleDriveError("Connect Google Drive before choosing a statement folder.")

        folder = self.drive.validate_empty_folder(connection, root_folder_id)
        root_folder_name = root_folder_name or folder.name
        accounts = list(FinancialAccount.objects.filter(user=user, is_active=True).select_related("user"))

        result = DriveActivationResult(connection=connection)
        with transaction.atomic():
            connection.root_folder_id = root_folder_id
            connection.root_folder_name = root_folder_name
            connection.is_active = True
            connection.activated_at = timezone.now()
            connection.disconnected_at = None
            connection.last_error = ""
            connection.save(
                update_fields=[
                    "root_folder_id",
                    "root_folder_name",
                    "is_active",
                    "activated_at",
                    "disconnected_at",
                    "last_error",
                    "updated_at",
                ]
            )

            for account in accounts:
                account_folder = self._create_account_folder(connection, account)
                result.account_folders_created += 1
                migrated, errors = self._migrate_account_statements(account, account_folder)
                result.statements_migrated += migrated
                result.errors.extend(errors)
                account.storage_uri = f"gdrive://{account_folder.folder_id}"
                account.save(update_fields=["storage_uri", "updated_at"])

            if result.errors:
                connection.last_error = "\n".join(result.errors[:10])
                connection.save(update_fields=["last_error", "updated_at"])

        return result

    def status(self, user: User) -> dict:
        connection = (
            GoogleDriveConnection.objects.filter(user=user).prefetch_related("account_folders__account").first()
        )
        if not connection:
            return {
                "configured": self._settings_configured(),
                "connected": False,
                "active": False,
                "account_folders": [],
            }
        return {
            "configured": self._settings_configured(),
            "connected": bool(connection.refresh_token_encrypted),
            "active": connection.is_active,
            "google_account_email": connection.google_account_email,
            "root_folder_id": connection.root_folder_id,
            "root_folder_name": connection.root_folder_name,
            "connected_at": connection.connected_at.isoformat() if connection.connected_at else None,
            "activated_at": connection.activated_at.isoformat() if connection.activated_at else None,
            "last_error": connection.last_error,
            "account_folders": [
                {
                    "account": folder.account_id,
                    "account_name": folder.account.name,
                    "folder_id": folder.folder_id,
                    "folder_name": folder.folder_name,
                    "storage_uri": f"gdrive://{folder.folder_id}",
                }
                for folder in connection.account_folders.all()
            ],
        }

    def disconnect_if_inactive(self, user: User) -> None:
        connection = GoogleDriveConnection.objects.filter(user=user).first()
        if not connection:
            return
        if connection.is_active:
            raise GoogleDriveError("Drive statement storage is active and cannot be disconnected.")
        connection.set_refresh_token("")
        connection.google_account_email = ""
        connection.disconnected_at = timezone.now()
        connection.save(
            update_fields=[
                "refresh_token_encrypted",
                "google_account_email",
                "disconnected_at",
                "updated_at",
            ]
        )

    def _create_account_folder(
        self,
        connection: GoogleDriveConnection,
        account: FinancialAccount,
    ) -> GoogleDriveAccountFolder:
        folder_name = self.drive.account_folder_name(account)
        folder = self.drive.create_folder(connection, parent_id=connection.root_folder_id, name=folder_name)
        return GoogleDriveAccountFolder.objects.create(
            connection=connection,
            account=account,
            folder_id=folder.id,
            folder_name=folder.name or folder_name,
        )

    def _migrate_account_statements(
        self,
        account: FinancialAccount,
        account_folder: GoogleDriveAccountFolder,
    ) -> tuple[int, list[str]]:
        statements = list(StatementFile.objects.filter(account=account, is_deleted=False))
        old_storage_uri = account.resolved_storage_uri()
        new_storage_uri = f"gdrive://{account_folder.folder_id}"
        if old_storage_uri == new_storage_uri:
            return 0, []

        migrated = 0
        errors: list[str] = []
        old_storage = get_storage(old_storage_uri)
        new_storage = get_storage(new_storage_uri)

        for statement in statements:
            try:
                old_relative = self.statement_files._stored_relative_path(statement.stored_path, old_storage_uri)
                with old_storage.open_file(old_storage_uri, old_relative) as handle:
                    content = handle.read()
                new_relative = self.statement_files._build_relative_path(
                    new_storage_uri,
                    statement.statement_year,
                    statement.statement_month,
                    statement.file_hash,
                    statement.original_filename,
                )
                stored = new_storage.write_file(new_storage_uri, new_relative, content)
                statement.stored_path = self.statement_files._stored_path_from_storage(
                    new_storage_uri,
                    stored.relative_path,
                )
                statement.save(update_fields=["stored_path", "updated_at"])
                migrated += 1
            except Exception as exc:
                logger.exception("Failed to migrate statement {} to Drive", statement.id)
                errors.append(f"{account.name}: {statement.original_filename}: {exc}")

        return migrated, errors

    def _settings_configured(self) -> bool:
        from django.conf import settings

        return bool(settings.GOOGLE_DRIVE_CLIENT_ID and settings.GOOGLE_DRIVE_CLIENT_SECRET)
