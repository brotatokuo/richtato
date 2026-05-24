"""Tests for Google Drive statement storage setup."""

from decimal import Decimal

import pytest

from apps.financial_account.models import FinancialAccount, GoogleDriveAccountFolder, GoogleDriveConnection
from apps.financial_account.services.account_service import AccountService
from apps.financial_account.services.google_drive_activation_service import GoogleDriveActivationService
from apps.financial_account.services.google_drive_service import (
    DRIVE_FOLDER_MIME_TYPE,
    DriveFileMetadata,
    GoogleDriveError,
)
from apps.richtato_user.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="drivetest", email="drive@test.com", password="x")


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Drive Checking",
        account_type="checking",
        balance=Decimal("0"),
        sync_mode="auto",
    )


class FakeDriveService:
    def validate_empty_folder(self, connection, folder_id):
        return DriveFileMetadata(
            id=folder_id,
            name="Richtato Statements",
            size=0,
            modified_time="",
            mime_type=DRIVE_FOLDER_MIME_TYPE,
        )

    def create_folder(self, connection, *, parent_id, name):
        return DriveFileMetadata(
            id=f"folder-{name}",
            name=name,
            size=0,
            modified_time="",
            mime_type=DRIVE_FOLDER_MIME_TYPE,
        )

    def account_folder_name(self, account):
        return f"{account.id}-Drive_Checking"


class TestGoogleDriveConnection:
    def test_refresh_token_is_encrypted_per_user(self, user):
        connection = GoogleDriveConnection.objects.create(user=user)

        connection.set_refresh_token("refresh-token")
        connection.save()

        connection.refresh_from_db()
        assert connection.refresh_token_encrypted != "refresh-token"
        assert connection.refresh_token == "refresh-token"


class TestGoogleDriveActivationService:
    def test_status_without_connection(self, user):
        status = GoogleDriveActivationService().status(user)

        assert status["connected"] is False
        assert status["active"] is False
        assert status["account_folders"] == []

    def test_activate_creates_account_folder_and_sets_storage_uri(self, user, account):
        connection = GoogleDriveConnection.objects.create(user=user, google_account_email="u@example.com")
        connection.set_refresh_token("refresh-token")
        connection.save()
        service = GoogleDriveActivationService()
        service.drive = FakeDriveService()

        result = service.activate(user, root_folder_id="root-folder")

        account.refresh_from_db()
        connection.refresh_from_db()
        folder = GoogleDriveAccountFolder.objects.get(account=account)
        assert result.account_folders_created == 1
        assert connection.is_active is True
        assert connection.root_folder_id == "root-folder"
        assert folder.folder_id == f"folder-{account.id}-Drive_Checking"
        assert account.storage_uri == f"gdrive://{folder.folder_id}"

    def test_deactivate_unlinks_folder_and_resets_storage_uri(self, user, account):
        connection = GoogleDriveConnection.objects.create(
            user=user,
            google_account_email="u@example.com",
            root_folder_id="root-folder",
            root_folder_name="Statements",
            is_active=True,
        )
        connection.set_refresh_token("refresh-token")
        connection.save()
        folder = GoogleDriveAccountFolder.objects.create(
            connection=connection,
            account=account,
            folder_id="drive-folder",
            folder_name=f"{account.id}-Drive_Checking",
        )
        account.storage_uri = f"gdrive://{folder.folder_id}"
        account.save(update_fields=["storage_uri"])

        service = GoogleDriveActivationService()
        result = service.deactivate(user)

        account.refresh_from_db()
        connection.refresh_from_db()
        assert result.account_folders_removed == 1
        assert connection.is_active is False
        assert connection.root_folder_id == ""
        assert connection.root_folder_name == ""
        assert account.storage_uri == ""
        assert not GoogleDriveAccountFolder.objects.filter(connection=connection).exists()

    def test_deactivate_requires_active_connection(self, user):
        GoogleDriveConnection.objects.create(user=user, google_account_email="u@example.com")
        service = GoogleDriveActivationService()

        with pytest.raises(GoogleDriveError, match="not active"):
            service.deactivate(user)

    def test_disconnect_requires_inactive_connection(self, user):
        GoogleDriveConnection.objects.create(
            user=user,
            google_account_email="u@example.com",
            is_active=True,
        )
        service = GoogleDriveActivationService()

        with pytest.raises(GoogleDriveError, match="Unlink the folder"):
            service.disconnect_if_inactive(user)


class TestAccountServiceDriveProvisioning:
    def test_create_account_with_active_drive_provisions_folder(self, user, monkeypatch):
        connection = GoogleDriveConnection.objects.create(
            user=user,
            google_account_email="u@example.com",
            root_folder_id="root-folder",
            root_folder_name="Statements",
            is_active=True,
        )
        connection.set_refresh_token("refresh-token")
        connection.save()

        import apps.financial_account.services.google_drive_activation_service as act_module

        # Replace the real GoogleDriveService with FakeDriveService so no HTTP calls are made
        monkeypatch.setattr(act_module, "GoogleDriveService", lambda: FakeDriveService())

        service = AccountService()
        account = service.create_manual_account(
            user=user,
            name="New Savings",
            account_type="savings",
        )

        account.refresh_from_db()
        drive_folder = GoogleDriveAccountFolder.objects.get(account=account)
        assert account.storage_uri == f"gdrive://{drive_folder.folder_id}"
        assert drive_folder.folder_id.startswith("folder-")

    def test_create_account_without_active_drive_leaves_storage_unconfigured(self, user):
        service = AccountService()
        account = service.create_manual_account(
            user=user,
            name="Local Checking",
            account_type="checking",
        )

        account.refresh_from_db()
        assert account.storage_uri == ""
        assert not GoogleDriveAccountFolder.objects.filter(account=account).exists()
