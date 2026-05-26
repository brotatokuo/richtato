"""Tests for Setup → Sync API and sync_mode updates."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.richtato_user.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="syncsetup", email="syncsetup@test.com", password="x")


@pytest.fixture
def robinhood_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(slug="robinhood", defaults={"name": "Robinhood"})
    return institution


@pytest.fixture
def amex_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="american_express",
        defaults={"name": "American Express"},
    )
    return institution


class TestBankSyncSetupAPIView:
    def test_returns_accounts_and_agent_config(self, user, robinhood_institution):
        account = FinancialAccount.objects.create(
            user=user,
            name="Robinhood Brokerage",
            account_type="investment",
            institution=robinhood_institution,
            sync_mode="auto",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse("account-sync-setup"))

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["accounts"]) == 1
        row = payload["accounts"][0]
        assert row["id"] == account.id
        assert row["sync_mode"] == "auto"
        assert row["agent_sync_supported"] is True
        assert row["agent_flow"] == "investment_balance"
        assert row["needs_storage_for_auto"] is False
        assert row["activity_url"] == ""
        assert row["has_activity_url"] is False
        assert row["needs_activity_url_for_auto"] is True
        assert row["agent_cadence"] == "daily"
        assert row["agent_sync_hour"] == 6
        assert payload["agent_config"]["logins"][0]["institution"] == "robinhood"
        assert payload["duplicate_institution_logins"] == []


class TestAccountSyncModeUpdate:
    def test_create_account_accepts_auto_sync_settings(self, user, robinhood_institution):
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            reverse("account-list-create"),
            {
                "name": "Robinhood Brokerage",
                "account_type": "investment",
                "institution_slug": robinhood_institution.slug,
                "sync_mode": "auto",
                "agent_cadence": "weekly",
                "agent_sync_hour": 9,
                "agent_activity_url": "https://robinhood.com/account?classic=1",
            },
            format="json",
        )

        assert response.status_code == 201
        account = FinancialAccount.objects.get(id=response.json()["id"])
        assert account.sync_mode == "auto"
        assert account.agent_cadence == "weekly"
        assert account.agent_sync_hour == 9
        assert account.agent_activity_url == "https://robinhood.com/account?classic=1"

    def test_create_account_rejects_auto_sync_for_unsupported_institution(self, user, amex_institution):
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            reverse("account-list-create"),
            {
                "name": "Amex Card",
                "account_type": "credit_card",
                "institution_slug": amex_institution.slug,
                "sync_mode": "auto",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "sync_mode" in response.json()

    def test_patch_sync_mode_auto_for_supported_account(self, user, robinhood_institution):
        account = FinancialAccount.objects.create(
            user=user,
            name="Robinhood Brokerage",
            account_type="investment",
            institution=robinhood_institution,
            sync_mode="manual",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch(
            reverse("account-detail", kwargs={"pk": account.id}),
            {"sync_mode": "auto"},
            format="json",
        )

        assert response.status_code == 200
        account.refresh_from_db()
        assert account.sync_mode == "auto"

    def test_patch_sync_mode_auto_rejects_unsupported_institution(self, user, amex_institution):
        account = FinancialAccount.objects.create(
            user=user,
            name="Amex Card",
            account_type="credit_card",
            institution=amex_institution,
            sync_mode="manual",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch(
            reverse("account-detail", kwargs={"pk": account.id}),
            {"sync_mode": "auto"},
            format="json",
        )

        assert response.status_code == 400
        assert "sync_mode" in response.json()
        account.refresh_from_db()
        assert account.sync_mode == "manual"


class TestAccountScheduleUpdate:
    def test_patch_agent_schedule_fields(self, user, robinhood_institution):
        account = FinancialAccount.objects.create(
            user=user,
            name="Robinhood Brokerage",
            account_type="investment",
            institution=robinhood_institution,
            sync_mode="auto",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch(
            reverse("account-detail", kwargs={"pk": account.id}),
            {"agent_cadence": "weekly", "agent_sync_hour": 9},
            format="json",
        )

        assert response.status_code == 200
        account.refresh_from_db()
        assert account.agent_cadence == "weekly"
        assert account.agent_sync_hour == 9

    def test_patch_agent_activity_url(self, user, robinhood_institution):
        account = FinancialAccount.objects.create(
            user=user,
            name="Robinhood Brokerage",
            account_type="investment",
            institution=robinhood_institution,
            sync_mode="auto",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch(
            reverse("account-detail", kwargs={"pk": account.id}),
            {"agent_activity_url": "https://robinhood.com/account?classic=1"},
            format="json",
        )

        assert response.status_code == 200
        account.refresh_from_db()
        assert account.agent_activity_url == "https://robinhood.com/account?classic=1"

    def test_sync_setup_reports_duplicate_institution_logins(self, user):
        chase, _ = FinancialInstitution.objects.get_or_create(slug="chase", defaults={"name": "Chase"})
        FinancialAccount.objects.create(
            user=user,
            name="Chase Checking",
            account_type="checking",
            institution=chase,
            sync_mode="auto",
            agent_cadence="daily",
            agent_sync_hour=6,
        )
        FinancialAccount.objects.create(
            user=user,
            name="Chase Savings",
            account_type="savings",
            institution=chase,
            sync_mode="auto",
            agent_cadence="weekly",
            agent_sync_hour=7,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse("account-sync-setup"))

        assert response.status_code == 200
        payload = response.json()
        assert payload["duplicate_institution_logins"] == ["chase"]
        assert len(payload["agent_config"]["logins"]) == 2
