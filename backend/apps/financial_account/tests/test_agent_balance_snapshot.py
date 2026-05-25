"""Tests for POST /accounts/agent-balances/."""

from decimal import Decimal

from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount, FinancialInstitution
from apps.richtato_user.models import User


class TestAgentBalanceSnapshotAPI(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="agentbal", email="agentbal@test.com", password="x")
        self.token = Token.objects.create(user=self.user)
        self.institution, _ = FinancialInstitution.objects.get_or_create(
            slug="guideline",
            defaults={"name": "Guideline"},
        )
        self.account = FinancialAccount.objects.create(
            user=self.user,
            name="401(k)",
            account_type="investment",
            institution=self.institution,
            balance=Decimal("1000.00"),
            sync_mode="auto",
        )
        self.client = APIClient()
        self.url = "/api/v1/accounts/agent-balances/"

    def test_token_auth_updates_balance(self):
        response = self.client.post(
            self.url,
            {"account_id": self.account.id, "balance": "46842.67", "date": "2026-05-25"},
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("46842.67"))

    def test_creates_history_with_agent_sync_source(self):
        self.client.post(
            self.url,
            {"account_id": self.account.id, "balance": "46842.67", "date": "2026-05-25"},
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        history = AccountBalanceHistory.objects.get(account=self.account, date="2026-05-25")
        self.assertEqual(history.balance, Decimal("46842.67"))
        self.assertEqual(history.source, "agent_sync")

    def test_other_users_account_returns_404(self):
        other_user = User.objects.create_user(username="other", email="other@test.com", password="x")
        other_token = Token.objects.create(user=other_user)
        response = self.client.post(
            self.url,
            {"account_id": self.account.id, "balance": "1.00", "date": "2026-05-25"},
            format="json",
            HTTP_AUTHORIZATION=f"Token {other_token.key}",
        )
        self.assertEqual(response.status_code, 404)

    def test_missing_fields_returns_400(self):
        response = self.client.post(
            self.url,
            {"account_id": self.account.id},
            format="json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 400)
