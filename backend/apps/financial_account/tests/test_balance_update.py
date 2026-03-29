"""Tests for AccountBalanceUpdateAPIView (set absolute balance)."""

from datetime import date
from decimal import Decimal

import pytest
from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class TestAccountBalanceUpdateAPI(TestCase):
    """Test the balance-setting endpoint POST /accounts/details/."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="apitest", email="api@test.com", password="testpass123"
        )
        self.account = FinancialAccount.objects.create(
            user=self.user,
            name="API Test Checking",
            account_type="checking",
            balance=Decimal("3000.00"),
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/v1/accounts/details/"

    def test_set_balance_updates_account(self):
        response = self.client.post(
            self.url,
            {"account": self.account.id, "balance": "5200.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("5200.00"))

    def test_set_balance_creates_history_entry(self):
        self.client.post(
            self.url,
            {"account": self.account.id, "balance": "4500.00", "date": "2025-06-15"},
            format="json",
        )
        history = AccountBalanceHistory.objects.get(
            account=self.account, date="2025-06-15"
        )
        self.assertEqual(history.balance, Decimal("4500.00"))

    def test_set_balance_response_format(self):
        response = self.client.post(
            self.url,
            {"account": self.account.id, "balance": "7777.77", "date": "2025-06-15"},
            format="json",
        )
        data = response.json()
        self.assertIn("balance", data)
        self.assertIn("date", data)
        self.assertEqual(data["balance"], "7777.77")

    def test_set_negative_balance(self):
        """Credit card accounts may have negative balances."""
        response = self.client.post(
            self.url,
            {"account": self.account.id, "balance": "-1500.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("-1500.00"))

    def test_missing_account_returns_400(self):
        response = self.client.post(
            self.url,
            {"balance": "1000.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_balance_returns_400(self):
        response = self.client.post(
            self.url,
            {"account": self.account.id, "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_date_returns_400(self):
        response = self.client.post(
            self.url,
            {"account": self.account.id, "balance": "1000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_account_returns_404(self):
        response = self.client.post(
            self.url,
            {"account": 99999, "balance": "1000.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_other_users_account_returns_404(self):
        other_user = User.objects.create_user(
            username="other", email="other@test.com", password="testpass123"
        )
        other_account = FinancialAccount.objects.create(
            user=other_user,
            name="Other Account",
            account_type="savings",
            balance=Decimal("9000.00"),
        )
        response = self.client.post(
            self.url,
            {"account": other_account.id, "balance": "1.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_403(self):
        anon_client = APIClient()
        response = anon_client.post(
            self.url,
            {"account": self.account.id, "balance": "1000.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertIn(response.status_code, [401, 403])

    def test_set_balance_overwrites_previous_history(self):
        """Setting balance twice on the same date should overwrite."""
        self.client.post(
            self.url,
            {"account": self.account.id, "balance": "1000.00", "date": "2025-06-15"},
            format="json",
        )
        self.client.post(
            self.url,
            {"account": self.account.id, "balance": "2000.00", "date": "2025-06-15"},
            format="json",
        )
        entries = AccountBalanceHistory.objects.filter(
            account=self.account, date="2025-06-15"
        )
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().balance, Decimal("2000.00"))
