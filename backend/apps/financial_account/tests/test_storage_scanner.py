"""Tests for the storage scanner that auto-imports Google Drive statement files."""

from decimal import Decimal

import pytest

from apps.financial_account.models import FinancialAccount, FinancialInstitution, StatementFile
from apps.financial_account.services.storage_scanner_service import StorageScannerService
from apps.financial_account.tests.fake_gdrive_storage import FakeGoogleDriveStorage
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


@pytest.fixture
def fake_drive_storage(monkeypatch):
    storage = FakeGoogleDriveStorage()
    monkeypatch.setattr(
        "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
        lambda: storage,
    )
    return storage


@pytest.fixture
def user(db):
    return User.objects.create_user(username="scantest", email="scan@test.com", password="x")


@pytest.fixture
def chase_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(slug="chase", defaults={"name": "Chase"})
    return institution


@pytest.fixture
def bofa_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="bank_of_america",
        defaults={"name": "Bank of America"},
    )
    return institution


@pytest.fixture
def chase_account(user, chase_institution):
    account = FinancialAccount.objects.create(
        user=user,
        name="Scan Chase Checking",
        account_type="checking",
        balance=Decimal("1000.00"),
        institution=chase_institution,
        storage_uri="gdrive://chase-folder",
    )
    return account


@pytest.fixture
def bofa_account(user, bofa_institution):
    account = FinancialAccount.objects.create(
        user=user,
        name="Scan BoFA Checking",
        account_type="checking",
        balance=Decimal("500.00"),
        institution=bofa_institution,
        storage_uri="gdrive://bofa-folder",
    )
    return account


def _write_drop(fake_drive_storage: FakeGoogleDriveStorage, account: FinancialAccount, filename: str, content: bytes):
    folder_id = account.storage_uri.replace("gdrive://", "")
    fake_drive_storage.files_by_folder.setdefault(folder_id, {})[filename] = content


CHASE_CSV = b"Transaction Date,Description,Amount\n2025-06-01,Coffee Shop,-5.00\n2025-06-02,Paycheck,1500.00\n"

BOFA_CSV = b"Posted Date,Payee,Amount\n2025-06-01,Grocery,-25.00\n2025-06-02,Refund,15.00\n"


class TestStorageScannerService:
    def test_scan_imports_dropped_chase_csv(self, chase_account, fake_drive_storage):
        _write_drop(fake_drive_storage, chase_account, "june.csv", CHASE_CSV)
        service = StorageScannerService()

        result = service.scan_account(chase_account.id)

        assert result.accounts_scanned == 1
        assert result.files_seen == 1
        assert result.files_imported == 1
        assert result.files_skipped == 0
        assert result.files_failed == 0

        statement = StatementFile.objects.get(account=chase_account)
        assert statement.source == "agent_drop"
        assert statement.institution == "chase"
        assert statement.import_status == "imported"
        assert statement.imported_count == 2

        assert Transaction.objects.filter(account=chase_account, sync_source="csv").count() == 2

    def test_scan_maps_bank_of_america_slug_to_bofa_parser(self, bofa_account, fake_drive_storage):
        _write_drop(fake_drive_storage, bofa_account, "june.csv", BOFA_CSV)
        service = StorageScannerService()

        result = service.scan_account(bofa_account.id)

        assert result.files_imported == 1
        statement = StatementFile.objects.get(account=bofa_account)
        assert statement.institution == "bofa"
        assert statement.import_status == "imported"
        assert Transaction.objects.filter(account=bofa_account, sync_source="csv").count() == 2

    def test_rescan_is_idempotent(self, chase_account, fake_drive_storage):
        _write_drop(fake_drive_storage, chase_account, "june.csv", CHASE_CSV)
        service = StorageScannerService()

        first = service.scan_account(chase_account.id)
        second = service.scan_account(chase_account.id)

        assert first.files_imported == 1
        assert second.files_imported == 0
        assert second.files_skipped == 1
        assert StatementFile.objects.filter(account=chase_account).count() == 1
        assert Transaction.objects.filter(account=chase_account, sync_source="csv").count() == 2

    def test_dry_run_does_not_create_statement_or_transactions(self, chase_account, fake_drive_storage):
        _write_drop(fake_drive_storage, chase_account, "june.csv", CHASE_CSV)
        service = StorageScannerService()

        result = service.scan_account(chase_account.id, dry_run=True)

        assert result.files_seen == 1
        assert result.files_imported == 0
        assert StatementFile.objects.filter(account=chase_account).count() == 0
        assert Transaction.objects.filter(account=chase_account, sync_source="csv").count() == 0
        assert any(outcome.status == "discovered" for outcome in result.outcomes)

    def test_account_without_institution_is_skipped_gracefully(self, user, fake_drive_storage):
        manual_account = FinancialAccount.objects.create(
            user=user,
            name="Manual",
            account_type="checking",
            balance=Decimal("0"),
            storage_uri="gdrive://manual-folder",
        )
        _write_drop(fake_drive_storage, manual_account, "june.csv", CHASE_CSV)

        result = StorageScannerService().scan_account(manual_account.id)

        assert result.files_failed == 1
        assert result.files_imported == 0
        assert StatementFile.objects.filter(account=manual_account).count() == 0

    def test_scan_skips_unsupported_extension(self, chase_account, fake_drive_storage):
        _write_drop(fake_drive_storage, chase_account, "notes.txt", b"hello")
        result = StorageScannerService().scan_account(chase_account.id)
        assert result.files_seen == 0

    def test_scan_skips_account_without_drive_storage(self, user, chase_institution):
        account = FinancialAccount.objects.create(
            user=user,
            name="No Drive",
            account_type="checking",
            balance=Decimal("0"),
            institution=chase_institution,
        )
        result = StorageScannerService().scan_account(account.id)
        assert result.files_seen == 0
        assert result.files_imported == 0
