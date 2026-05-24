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
)
from apps.financial_account.services.google_drive_service import GoogleDriveError, GoogleDriveService
from apps.richtato_user.models import User


@dataclass
class DriveActivationResult:
    """Summary of a Drive activation run."""

    connection: GoogleDriveConnection
    account_folders_created: int = 0
    errors: list[str] = field(default_factory=list)


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

    def _settings_configured(self) -> bool:
        from django.conf import settings

        return bool(settings.GOOGLE_DRIVE_CLIENT_ID and settings.GOOGLE_DRIVE_CLIENT_SECRET)
