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
    existing_subfolders: dict[str, list[DriveFileMetadata]] = {}
    folder_files: dict[str, list[DriveFileMetadata]] = {}

    def validate_empty_folder(self, connection, folder_id):
        children = self.existing_subfolders.get(folder_id, [])
        if children:
            raise GoogleDriveError("Selected Drive folder must be empty.")
        return self.validate_folder(connection, folder_id)

    def validate_folder(self, connection, folder_id):
        return DriveFileMetadata(
            id=folder_id,
            name="Richtato Statements",
            size=0,
            modified_time="",
            mime_type=DRIVE_FOLDER_MIME_TYPE,
        )

    def list_files(self, connection, folder_id, *, include_folders=False):
        if include_folders:
            return list(self.existing_subfolders.get(folder_id, []))
        return list(self.folder_files.get(folder_id, []))

    def create_folder(self, connection, *, parent_id, name):
        folder = DriveFileMetadata(
            id=f"folder-{name}",
            name=name,
            size=0,
            modified_time="",
            mime_type=DRIVE_FOLDER_MIME_TYPE,
        )
        self.existing_subfolders.setdefault(parent_id, []).append(folder)
        return folder

    def account_folder_name(self, account):
        return f"{account.id}-Drive_Checking"


@pytest.fixture(autouse=True)
def reset_fake_drive_state():
    FakeDriveService.existing_subfolders = {}
    FakeDriveService.folder_files = {}
    yield
    FakeDriveService.existing_subfolders = {}
    FakeDriveService.folder_files = {}


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

    def test_preview_adopt_existing_matches_account_folders(self, user, account):
        connection = GoogleDriveConnection.objects.create(user=user, google_account_email="u@example.com")
        connection.set_refresh_token("refresh-token")
        connection.save()
        FakeDriveService.existing_subfolders["root-folder"] = [
            DriveFileMetadata(
                id="existing-folder",
                name=f"{account.id}-Drive_Checking",
                size=0,
                modified_time="",
                mime_type=DRIVE_FOLDER_MIME_TYPE,
            ),
            DriveFileMetadata(
                id="stale-folder",
                name="99-Old_Account",
                size=0,
                modified_time="",
                mime_type=DRIVE_FOLDER_MIME_TYPE,
            ),
        ]
        FakeDriveService.folder_files["existing-folder"] = [
            DriveFileMetadata(
                id="file-1",
                name="statement.csv",
                size=10,
                modified_time="",
                mime_type="text/csv",
            )
        ]

        service = GoogleDriveActivationService()
        service.drive = FakeDriveService()
        preview = service.preview_adopt_existing(user, root_folder_id="root-folder")

        assert preview.adopted == [
            {
                "account_id": account.id,
                "account_name": account.name,
                "folder_id": "existing-folder",
                "folder_name": f"{account.id}-Drive_Checking",
                "statement_file_count": 1,
            }
        ]
        assert preview.would_create == []
        assert preview.unmatched == [
            {
                "folder_id": "stale-folder",
                "folder_name": "99-Old_Account",
                "parsed_account_id": 99,
            }
        ]
        assert preview.errors == []

    def test_activate_adopt_existing_links_folders_and_creates_missing(self, user, account):
        connection = GoogleDriveConnection.objects.create(user=user, google_account_email="u@example.com")
        connection.set_refresh_token("refresh-token")
        connection.save()
        second_account = FinancialAccount.objects.create(
            user=user,
            name="Drive Savings",
            account_type="savings",
            balance=Decimal("0"),
            sync_mode="auto",
        )
        FakeDriveService.existing_subfolders["root-folder"] = [
            DriveFileMetadata(
                id="existing-folder",
                name=f"{account.id}-Drive_Checking",
                size=0,
                modified_time="",
                mime_type=DRIVE_FOLDER_MIME_TYPE,
            )
        ]

        service = GoogleDriveActivationService()
        service.drive = FakeDriveService()
        result = service.activate(user, root_folder_id="root-folder", adopt_existing=True)

        account.refresh_from_db()
        second_account.refresh_from_db()
        connection.refresh_from_db()
        adopted_folder = GoogleDriveAccountFolder.objects.get(account=account)
        created_folder = GoogleDriveAccountFolder.objects.get(account=second_account)

        assert result.account_folders_adopted == 1
        assert result.account_folders_created == 1
        assert connection.is_active is True
        assert adopted_folder.folder_id == "existing-folder"
        assert account.storage_uri == "gdrive://existing-folder"
        assert created_folder.folder_id == f"folder-{second_account.id}-Drive_Checking"
        assert second_account.storage_uri == f"gdrive://{created_folder.folder_id}"

    def test_preview_adopt_existing_reports_duplicate_account_prefix(self, user, account):
        connection = GoogleDriveConnection.objects.create(user=user, google_account_email="u@example.com")
        connection.set_refresh_token("refresh-token")
        connection.save()
        FakeDriveService.existing_subfolders["root-folder"] = [
            DriveFileMetadata(
                id="folder-a",
                name=f"{account.id}-Drive_Checking",
                size=0,
                modified_time="",
                mime_type=DRIVE_FOLDER_MIME_TYPE,
            ),
            DriveFileMetadata(
                id="folder-b",
                name=f"{account.id}-Duplicate",
                size=0,
                modified_time="",
                mime_type=DRIVE_FOLDER_MIME_TYPE,
            ),
        ]

        service = GoogleDriveActivationService()
        service.drive = FakeDriveService()
        preview = service.preview_adopt_existing(user, root_folder_id="root-folder")

        assert preview.adopted == [
            {
                "account_id": account.id,
                "account_name": account.name,
                "folder_id": "folder-a",
                "folder_name": f"{account.id}-Drive_Checking",
                "statement_file_count": 0,
            }
        ]
        assert preview.errors[0]["message"].startswith(f"Duplicate account folder prefix {account.id}")

    def test_activate_adopt_existing_rejects_duplicate_prefix(self, user, account):
        connection = GoogleDriveConnection.objects.create(user=user, google_account_email="u@example.com")
        connection.set_refresh_token("refresh-token")
        connection.save()
        FakeDriveService.existing_subfolders["root-folder"] = [
            DriveFileMetadata(
                id="folder-a",
                name=f"{account.id}-Drive_Checking",
                size=0,
                modified_time="",
                mime_type=DRIVE_FOLDER_MIME_TYPE,
            ),
            DriveFileMetadata(
                id="folder-b",
                name=f"{account.id}-Duplicate",
                size=0,
                modified_time="",
                mime_type=DRIVE_FOLDER_MIME_TYPE,
            ),
        ]

        service = GoogleDriveActivationService()
        service.drive = FakeDriveService()

        with pytest.raises(GoogleDriveError, match="Duplicate account folder prefix"):
            service.activate(user, root_folder_id="root-folder", adopt_existing=True)


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
