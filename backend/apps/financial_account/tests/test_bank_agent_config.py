"""Tests for generated bank-agent configuration."""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.financial_account.services.bank_agent_config_service import BankAgentConfigOptions, BankAgentConfigService
from apps.richtato_user.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="agentconfig", email="agentconfig@test.com", password="x")


@pytest.fixture
def bofa_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="bank_of_america",
        defaults={"name": "Bank of America"},
    )
    return institution


@pytest.fixture
def chase_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(slug="chase", defaults={"name": "Chase"})
    return institution


@pytest.fixture
def guideline_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(slug="guideline", defaults={"name": "Guideline"})
    return institution


def _account(
    user,
    institution,
    *,
    name: str,
    account_type: str = "checking",
    sync_mode: str = "auto",
):
    return FinancialAccount.objects.create(
        user=user,
        name=name,
        account_type=account_type,
        balance=Decimal("0"),
        institution=institution,
        sync_mode=sync_mode,
    )


class TestBankAgentConfigService:
    def test_builds_config_from_active_auto_accounts(self, user, bofa_institution, chase_institution):
        checking = _account(user, bofa_institution, name="Advantage Checking")
        credit_card = _account(user, chase_institution, name="Sapphire", account_type="credit_card")
        _account(user, bofa_institution, name="Manual Only", sync_mode="manual")

        config = BankAgentConfigService().build_for_user(user)

        assert config["version"] == 1
        assert config["user_id"] == user.id
        assert [login["institution"] for login in config["logins"]] == ["bofa", "chase"]
        bofa_login = config["logins"][0]
        chase_login = config["logins"][1]
        assert bofa_login["accounts"] == [
            {
                "name": checking.name,
                "flow": "deposit",
                "storage_uri": checking.resolved_storage_uri(),
                "richtato_account_id": checking.id,
            }
        ]
        assert chase_login["accounts"][0]["name"] == credit_card.name
        assert chase_login["accounts"][0]["flow"] == "credit_card"

    def test_guideline_investment_uses_investment_balance_flow(self, user, guideline_institution):
        account = _account(
            user,
            guideline_institution,
            name="401(k)",
            account_type="investment",
        )

        config = BankAgentConfigService().build_for_user(user)

        assert config["logins"] == [
            {
                "institution": "guideline",
                "nickname": "personal",
                "cadence": "daily",
                "hour": 6,
                "accounts": [
                    {
                        "name": account.name,
                        "flow": "investment_balance",
                        "storage_uri": account.resolved_storage_uri(),
                        "richtato_account_id": account.id,
                    }
                ],
            }
        ]

    def test_can_include_all_supported_accounts(self, user, bofa_institution):
        manual = _account(user, bofa_institution, name="Manual Supported", sync_mode="manual")

        config = BankAgentConfigService().build_for_user(
            user,
            BankAgentConfigOptions(include_all_supported=True),
        )

        assert config["logins"][0]["accounts"][0]["richtato_account_id"] == manual.id


class TestBankAgentConfigAPIView:
    def test_returns_generated_config_for_authenticated_user(self, user, bofa_institution):
        account = _account(user, bofa_institution, name="Auto Checking")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse("account-bank-agent-config"),
            {"cadence": "weekly", "hour": "7", "nickname": "primary"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["logins"][0]["institution"] == "bofa"
        assert payload["logins"][0]["cadence"] == "weekly"
        assert payload["logins"][0]["hour"] == 7
        assert payload["logins"][0]["nickname"] == "primary"
        assert payload["logins"][0]["accounts"][0]["storage_uri"] == account.resolved_storage_uri()
