"""Tests for Google Drive statement storage setup."""

from decimal import Decimal

import pytest

from apps.financial_account.models import FinancialAccount, GoogleDriveAccountFolder, GoogleDriveConnection
from apps.financial_account.services.google_drive_activation_service import GoogleDriveActivationService
from apps.financial_account.services.google_drive_service import DRIVE_FOLDER_MIME_TYPE, DriveFileMetadata
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
