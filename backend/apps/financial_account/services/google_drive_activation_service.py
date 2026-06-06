"""Activate Google Drive as the canonical statement store."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from loguru import logger

from apps.financial_account.models import (
    FinancialAccount,
    GoogleDriveAccountFolder,
    GoogleDriveConnection,
)
from apps.financial_account.services.google_drive_service import (
    DRIVE_FOLDER_MIME_TYPE,
    DriveFileMetadata,
    GoogleDriveError,
    GoogleDriveService,
)
from apps.richtato_user.models import User

ACCOUNT_FOLDER_ID_PREFIX = re.compile(r"^(\d+)-")
STATEMENT_EXTENSIONS = {".csv", ".xls", ".xlsx"}


@dataclass
class DriveActivationResult:
    """Summary of a Drive activation run."""

    connection: GoogleDriveConnection
    account_folders_created: int = 0
    account_folders_adopted: int = 0
    unmatched_drive_folders: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scan_summary: dict | None = None


@dataclass
class DriveAdoptPreview:
    """Dry-run summary for adopting an existing Drive root."""

    root_folder_id: str
    root_folder_name: str
    adopted: list[dict] = field(default_factory=list)
    would_create: list[dict] = field(default_factory=list)
    unmatched: list[dict] = field(default_factory=list)
    statement_file_counts: dict[str, int] = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)


@dataclass
class DriveDeactivationResult:
    """Summary of unlinking an active Drive statement root."""

    connection: GoogleDriveConnection
    account_folders_removed: int = 0
    errors: list[str] = field(default_factory=list)


class GoogleDriveActivationService:
    """Create account folders and switch accounts to Google Drive storage."""

    def __init__(self):
        self.drive = GoogleDriveService()

    def activate(
        self,
        user: User,
        *,
        root_folder_id: str,
        root_folder_name: str = "",
        adopt_existing: bool = False,
        scan_after_adopt: bool = False,
    ) -> DriveActivationResult:
        connection = GoogleDriveConnection.objects.filter(user=user).first()
        if not connection:
            raise GoogleDriveError("Connect Google Drive before choosing a statement folder.")

        if adopt_existing:
            folder = self.drive.validate_folder(connection, root_folder_id)
        else:
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

            if adopt_existing:
                preview = self.preview_adopt_existing(user, root_folder_id=root_folder_id)
                if preview.errors:
                    raise GoogleDriveError(preview.errors[0]["message"])

                adopted_by_account_id = {item["account_id"]: item for item in preview.adopted}
                result.unmatched_drive_folders = preview.unmatched

                for account in accounts:
                    adopted = adopted_by_account_id.get(account.id)
                    try:
                        if adopted:
                            account_folder = self._link_existing_folder(
                                connection,
                                account,
                                folder_id=adopted["folder_id"],
                                folder_name=adopted["folder_name"],
                            )
                            result.account_folders_adopted += 1
                        else:
                            account_folder = self._create_account_folder(connection, account)
                            result.account_folders_created += 1
                        account.storage_uri = f"gdrive://{account_folder.folder_id}"
                        account.save(update_fields=["storage_uri", "updated_at"])
                    except Exception as exc:
                        msg = f"{account.name}: {exc}"
                        result.errors.append(msg)
                        logger.exception("Failed to link Drive folder for account {} during adopt", account.id)
            else:
                for account in accounts:
                    try:
                        account_folder = self._create_account_folder(connection, account)
                        result.account_folders_created += 1
                        account.storage_uri = f"gdrive://{account_folder.folder_id}"
                        account.save(update_fields=["storage_uri", "updated_at"])
                    except Exception as exc:
                        msg = f"{account.name}: {exc}"
                        result.errors.append(msg)
                        logger.exception("Failed to create Drive folder for account {} during activation", account.id)

            if result.errors:
                connection.last_error = "\n".join(result.errors[:10])
                connection.save(update_fields=["last_error", "updated_at"])

        if adopt_existing and scan_after_adopt and not result.errors:
            from apps.financial_account.services.storage_scanner_service import StorageScannerService

            scan_result = StorageScannerService().scan_user(user.id)
            result.scan_summary = {
                "accounts_scanned": scan_result.accounts_scanned,
                "files_seen": scan_result.files_seen,
                "files_imported": scan_result.files_imported,
                "files_skipped": scan_result.files_skipped,
                "files_failed": scan_result.files_failed,
                "files_removed": scan_result.files_removed,
            }

        return result

    def preview_adopt_existing(self, user: User, *, root_folder_id: str) -> DriveAdoptPreview:
        connection = GoogleDriveConnection.objects.filter(user=user).first()
        if not connection:
            raise GoogleDriveError("Connect Google Drive before choosing a statement folder.")

        folder = self.drive.validate_folder(connection, root_folder_id)
        accounts = list(FinancialAccount.objects.filter(user=user, is_active=True).select_related("user"))
        adopted, would_create, unmatched, errors = self._build_adopt_plan(connection, folder, accounts)

        statement_file_counts = {
            item["folder_id"]: item["statement_file_count"] for item in adopted if item.get("folder_id")
        }

        return DriveAdoptPreview(
            root_folder_id=folder.id,
            root_folder_name=folder.name,
            adopted=adopted,
            would_create=would_create,
            unmatched=unmatched,
            statement_file_counts=statement_file_counts,
            errors=[{"message": message} for message in errors],
        )

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
        folder_account_ids = {folder.account_id for folder in connection.account_folders.all()}
        total_active = FinancialAccount.objects.filter(user=user, is_active=True).count()
        missing_folder_count = max(0, total_active - len(folder_account_ids)) if connection.is_active else 0
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
            "missing_folder_count": missing_folder_count,
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

    def deactivate(self, user: User) -> DriveDeactivationResult:
        """Unlink the active Drive root and clear account storage URIs."""
        connection = (
            GoogleDriveConnection.objects.filter(user=user).prefetch_related("account_folders__account").first()
        )
        if not connection or not connection.is_active:
            raise GoogleDriveError("Drive statement storage is not active.")

        accounts = list(FinancialAccount.objects.filter(user=user, is_active=True).select_related("user"))
        folders_by_account = {
            folder.account_id: folder for folder in connection.account_folders.select_related("account").all()
        }
        result = DriveDeactivationResult(connection=connection)

        with transaction.atomic():
            for account in accounts:
                folder = folders_by_account.get(account.id)
                if not folder and not account.storage_uri.startswith("gdrive://"):
                    continue

                account.storage_uri = ""
                account.save(update_fields=["storage_uri", "updated_at"])
                if folder:
                    result.account_folders_removed += 1

            connection.account_folders.all().delete()
            connection.root_folder_id = ""
            connection.root_folder_name = ""
            connection.is_active = False
            connection.last_error = ""
            connection.save(
                update_fields=[
                    "root_folder_id",
                    "root_folder_name",
                    "is_active",
                    "last_error",
                    "updated_at",
                ]
            )

        return result

    def sync_missing_folders(self, user: User) -> DriveActivationResult:
        """Create Drive folders for any active accounts that don't have one yet.

        Safe to call at any time while Drive is active — already-provisioned
        accounts are skipped.
        """
        connection = GoogleDriveConnection.objects.filter(user=user, is_active=True).first()
        if not connection:
            raise GoogleDriveError("Drive statement storage is not active.")

        result = DriveActivationResult(connection=connection)
        existing_account_ids = set(connection.account_folders.values_list("account_id", flat=True))
        accounts = list(
            FinancialAccount.objects.filter(user=user, is_active=True)
            .exclude(id__in=existing_account_ids)
            .select_related("user")
        )

        with transaction.atomic():
            for account in accounts:
                try:
                    account_folder = self._create_account_folder(connection, account)
                    result.account_folders_created += 1
                    account.storage_uri = f"gdrive://{account_folder.folder_id}"
                    account.save(update_fields=["storage_uri", "updated_at"])
                    logger.info("Synced missing Drive folder {} for account {}", account_folder.folder_id, account.id)
                except Exception as exc:
                    msg = f"{account.name}: {exc}"
                    result.errors.append(msg)
                    logger.exception("Failed to create Drive folder for account {} during sync", account.id)

            if result.errors:
                connection.last_error = "\n".join(result.errors[:10])
                connection.save(update_fields=["last_error", "updated_at"])

        return result

    def disconnect_if_inactive(self, user: User) -> None:
        connection = GoogleDriveConnection.objects.filter(user=user).first()
        if not connection:
            return
        if connection.is_active:
            raise GoogleDriveError("Drive statement storage is active. Unlink the folder before disconnecting.")
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

    def _build_adopt_plan(
        self,
        connection: GoogleDriveConnection,
        root_folder: DriveFileMetadata,
        accounts: list[FinancialAccount],
    ) -> tuple[list[dict], list[dict], list[dict], list[str]]:
        children = self.drive.list_files(connection, root_folder.id, include_folders=True)
        subfolders = [item for item in children if item.mime_type == DRIVE_FOLDER_MIME_TYPE]

        folders_by_account_id: dict[int, DriveFileMetadata] = {}
        unmatched: list[dict] = []
        errors: list[str] = []

        for subfolder in subfolders:
            match = ACCOUNT_FOLDER_ID_PREFIX.match(subfolder.name)
            if not match:
                unmatched.append(
                    {
                        "folder_id": subfolder.id,
                        "folder_name": subfolder.name,
                        "parsed_account_id": None,
                    }
                )
                continue

            account_id = int(match.group(1))
            if account_id in folders_by_account_id:
                existing = folders_by_account_id[account_id]
                errors.append(
                    f"Duplicate account folder prefix {account_id}: '{existing.name}' and '{subfolder.name}'."
                )
                continue
            folders_by_account_id[account_id] = subfolder

        account_ids = {account.id for account in accounts}
        adopted: list[dict] = []
        would_create: list[dict] = []

        for account in accounts:
            subfolder = folders_by_account_id.get(account.id)
            if subfolder:
                adopted.append(
                    {
                        "account_id": account.id,
                        "account_name": account.name,
                        "folder_id": subfolder.id,
                        "folder_name": subfolder.name,
                        "statement_file_count": self._count_statement_files(connection, subfolder.id),
                    }
                )
            else:
                would_create.append(
                    {
                        "account_id": account.id,
                        "account_name": account.name,
                        "expected_folder_name": self.drive.account_folder_name(account),
                    }
                )

        for account_id, subfolder in folders_by_account_id.items():
            if account_id not in account_ids:
                unmatched.append(
                    {
                        "folder_id": subfolder.id,
                        "folder_name": subfolder.name,
                        "parsed_account_id": account_id,
                    }
                )

        return adopted, would_create, unmatched, errors

    def _count_statement_files(self, connection: GoogleDriveConnection, folder_id: str) -> int:
        files = self.drive.list_files(connection, folder_id)
        return sum(1 for item in files if Path(item.name).suffix.lower() in STATEMENT_EXTENSIONS)

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

    def _link_existing_folder(
        self,
        connection: GoogleDriveConnection,
        account: FinancialAccount,
        *,
        folder_id: str,
        folder_name: str,
    ) -> GoogleDriveAccountFolder:
        return GoogleDriveAccountFolder.objects.create(
            connection=connection,
            account=account,
            folder_id=folder_id,
            folder_name=folder_name,
        )

    def _settings_configured(self) -> bool:
        from django.conf import settings

        return bool(settings.GOOGLE_DRIVE_CLIENT_ID and settings.GOOGLE_DRIVE_CLIENT_SECRET)
