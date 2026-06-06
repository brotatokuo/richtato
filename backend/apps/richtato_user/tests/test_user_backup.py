"""Tests for user backup export and import."""

import csv
import io
import json
from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.budget.models import Budget, BudgetCategory
from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User, UserPreference
from apps.richtato_user.services.user_backup_export_service import UserBackupExportService
from apps.richtato_user.services.user_backup_import_service import UserBackupImportService
from apps.transaction.models import CategoryKeyword, Transaction, TransactionCategory


@pytest.fixture
def source_user(db):
    return User.objects.create_user(username="backup_source", email="source@test.com", password="testpass123")


@pytest.fixture
def target_user(db):
    return User.objects.create_user(username="backup_target", email="target@test.com", password="testpass123")


@pytest.fixture
def populated_user(source_user):
    UserPreference.objects.filter(user=source_user).update(
        theme="dark",
        currency="EUR",
        timezone="Europe/London",
    )

    groceries = TransactionCategory.objects.create(
        user=source_user,
        slug="backup-groceries",
        name="Backup Groceries",
        type="expense",
        icon="cart",
        color="#00ff00",
    )
    CategoryKeyword.objects.create(user=source_user, category=groceries, keyword="whole foods")

    account = FinancialAccount.objects.create(
        user=source_user,
        name="Main Checking",
        account_type="checking",
        balance=Decimal("1000.00"),
        currency="USD",
    )

    budget = Budget.objects.create(
        user=source_user,
        name="May Budget",
        period_type="monthly",
        start_date=date(2025, 5, 1),
        end_date=date(2025, 5, 31),
    )
    BudgetCategory.objects.create(
        budget=budget,
        category=groceries,
        allocated_amount=Decimal("400.00"),
    )

    Transaction.objects.create(
        user=source_user,
        account=account,
        date=date(2025, 5, 10),
        amount=Decimal("42.15"),
        description='Whole Foods, "fresh" produce',
        transaction_type="debit",
        category=groceries,
        status="posted",
        sync_source="manual",
        external_id="txn-001",
        categorization_status="categorized",
        notes="weekly shop",
    )

    return source_user


class TestUserBackupExportService:
    def test_build_json_bundle_shape(self, populated_user):
        bundle = UserBackupExportService().build_json_bundle(populated_user)

        assert bundle["format_version"] == 1
        assert bundle["app"] == "richtato"
        assert bundle["profile"]["username"] == "backup_source"
        assert bundle["preferences"]["theme"] == "dark"
        assert len(bundle["categories"]) >= 1
        assert len(bundle["accounts"]) == 1
        assert len(bundle["budgets"]) == 1
        assert len(bundle["transactions"]) == 1
        assert bundle["transactions"][0]["description"] == 'Whole Foods, "fresh" produce'

    def test_build_transactions_csv_escapes_commas(self, populated_user):
        csv_text = UserBackupExportService().build_transactions_csv(populated_user)
        rows = list(csv.reader(io.StringIO(csv_text)))

        assert rows[0] == [
            "date",
            "amount",
            "type",
            "description",
            "account_name",
            "category_slug",
            "status",
            "notes",
            "sync_source",
            "external_id",
        ]
        assert rows[1][3] == 'Whole Foods, "fresh" produce'
        assert rows[1][5] == "backup-groceries"


class TestUserBackupImportService:
    def test_rejects_non_empty_account(self, populated_user, target_user):
        FinancialAccount.objects.create(
            user=target_user,
            name="Existing",
            account_type="checking",
            balance=Decimal("0"),
        )
        bundle = UserBackupExportService().build_json_bundle(populated_user)
        service = UserBackupImportService()

        preview = service.preview(target_user, bundle)
        assert preview["valid"] is False
        assert any("accounts" in error for error in preview["errors"])

    def test_round_trip_restores_data(self, populated_user, target_user):
        export_service = UserBackupExportService()
        import_service = UserBackupImportService()
        bundle = export_service.build_json_bundle(populated_user)

        preview = import_service.preview(target_user, bundle)
        assert preview["valid"] is True

        result = import_service.commit(target_user, bundle)
        assert result["imported"]["accounts"] == 1
        assert result["imported"]["transactions"] == 1
        assert result["imported"]["budgets"] == 1

        account = FinancialAccount.objects.get(user=target_user)
        assert account.balance == Decimal("957.85")
        assert account.name == "Main Checking"

        txn = Transaction.objects.get(user=target_user)
        assert txn.description == 'Whole Foods, "fresh" produce'
        assert txn.external_id == "txn-001"
        assert txn.category.slug == "backup-groceries"

        prefs = UserPreference.objects.get(user=target_user)
        assert prefs.theme == "dark"
        assert prefs.currency == "EUR"


class TestUserBackupAPIViews:
    def test_export_json_download(self, populated_user):
        client = APIClient()
        client.force_authenticate(user=populated_user)

        response = client.get(reverse("backup_export"))

        assert response.status_code == 200
        assert response["Content-Type"].startswith("application/json")
        assert "attachment" in response["Content-Disposition"]
        payload = json.loads(response.content.decode())
        assert payload["format_version"] == 1
        assert len(payload["transactions"]) == 1

    def test_export_transactions_csv_download(self, populated_user):
        client = APIClient()
        client.force_authenticate(user=populated_user)

        response = client.get(reverse("backup_export_transactions"))

        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/csv")
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        assert len(rows) == 2

    def test_import_status_and_preview(self, populated_user, target_user):
        client = APIClient()
        client.force_authenticate(user=target_user)

        status_response = client.get(reverse("backup_import_status"))
        assert status_response.status_code == 200
        assert status_response.json()["can_import"] is True

        bundle = UserBackupExportService().build_json_bundle(populated_user)
        preview_response = client.post(
            reverse("backup_import_preview"),
            data={"file": io.BytesIO(json.dumps(bundle).encode("utf-8"))},
            format="multipart",
        )

        assert preview_response.status_code == 200
        preview = preview_response.json()
        assert preview["valid"] is True
        assert preview["counts"]["transactions"] == 1

    def test_import_commit_via_multipart(self, populated_user, target_user):
        client = APIClient()
        client.force_authenticate(user=target_user)

        bundle = UserBackupExportService().build_json_bundle(populated_user)
        response = client.post(
            reverse("backup_import_commit"),
            data={
                "file": io.BytesIO(json.dumps(bundle).encode("utf-8")),
                "confirm": "true",
            },
            format="multipart",
        )

        assert response.status_code == 200
        assert response.json()["imported"]["transactions"] == 1
        assert FinancialAccount.objects.filter(user=target_user).count() == 1
