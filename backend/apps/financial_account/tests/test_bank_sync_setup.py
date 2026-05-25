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
        assert payload["agent_config"]["logins"][0]["institution"] == "robinhood"


class TestAccountSyncModeUpdate:
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
