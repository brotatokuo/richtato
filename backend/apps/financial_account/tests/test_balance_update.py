"""Tests for AccountBalanceUpdateAPIView (balance on date reconciliation)."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.financial_account.models import AccountBalanceHistory, FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


class TestAccountBalanceUpdateAPI(TestCase):
    """Test the balance reconciliation endpoint POST /accounts/details/."""

    def setUp(self):
        self.user = User.objects.create_user(username="apitest", email="api@test.com", password="testpass123")
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

    def test_set_balance_creates_adjustment_transaction(self):
        response = self.client.post(
            self.url,
            {"account": self.account.id, "balance": "4500.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        adj = Transaction.objects.filter(
            account=self.account,
            description="Balance Adjustment",
        ).first()
        self.assertIsNotNone(adj)
        self.assertEqual(adj.amount, Decimal("1500.00"))
        self.assertEqual(adj.transaction_type, "credit")
        data = response.json()
        self.assertEqual(data["adjustment"], "1500.00")
        self.assertEqual(data["computed_balance"], "3000.00")
        self.assertIsNotNone(data["adjustment_transaction_id"])

    def test_set_balance_creates_history_entry(self):
        self.client.post(
            self.url,
            {"account": self.account.id, "balance": "4500.00", "date": "2025-06-15"},
            format="json",
        )
        history = AccountBalanceHistory.objects.get(account=self.account, date="2025-06-15")
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
        self.assertIn("computed_balance", data)
        self.assertIn("adjustment", data)
        self.assertIn("adjustment_transaction_id", data)
        self.assertIn("previous_balance", data)
        self.assertEqual(data["balance"], "7777.77")

    def test_matching_balance_creates_no_transaction(self):
        response = self.client.post(
            self.url,
            {"account": self.account.id, "balance": "3000.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Transaction.objects.filter(account=self.account, description="Balance Adjustment").exists()
        )
        data = response.json()
        self.assertEqual(data["adjustment"], "0.00")
        self.assertIsNone(data["adjustment_transaction_id"])

    def test_past_date_with_later_transactions(self):
        target_date = date.today() - timedelta(days=2)
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            date=date.today(),
            amount=Decimal("500.00"),
            transaction_type="credit",
            description="Deposit",
            sync_source="manual",
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("3500.00"))

        response = self.client.post(
            self.url,
            {
                "account": self.account.id,
                "balance": "2800.00",
                "date": target_date.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("3300.00"))
        data = response.json()
        self.assertEqual(data["computed_balance"], "3000.00")
        self.assertEqual(data["adjustment"], "-200.00")

    def test_set_negative_balance(self):
        response = self.client.post(
            self.url,
            {"account": self.account.id, "balance": "-1500.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("-1500.00"))

    def test_credit_card_account_returns_400(self):
        credit_card = FinancialAccount.objects.create(
            user=self.user,
            name="API Test Card",
            account_type="credit_card",
            balance=Decimal("-500.00"),
            is_liability=True,
        )
        response = self.client.post(
            self.url,
            {"account": credit_card.id, "balance": "-600.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_savings_account_allowed(self):
        savings = FinancialAccount.objects.create(
            user=self.user,
            name="API Test Savings",
            account_type="savings",
            balance=Decimal("10000.00"),
        )
        response = self.client.post(
            self.url,
            {"account": savings.id, "balance": "10500.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_investment_account_allowed(self):
        investment = FinancialAccount.objects.create(
            user=self.user,
            name="API Test Investment",
            account_type="investment",
            balance=Decimal("25000.00"),
        )
        response = self.client.post(
            self.url,
            {"account": investment.id, "balance": "26000.00", "date": "2025-06-15"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_future_date_returns_400(self):
        future = (date.today() + timedelta(days=1)).isoformat()
        response = self.client.post(
            self.url,
            {"account": self.account.id, "balance": "1000.00", "date": future},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

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
        other_user = User.objects.create_user(username="other", email="other@test.com", password="testpass123")
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

    def test_second_reconciliation_on_same_date(self):
        """A second reconciliation on the same date creates another adjustment."""
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
        entries = AccountBalanceHistory.objects.filter(account=self.account, date="2025-06-15")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().balance, Decimal("2000.00"))
        self.assertEqual(
            Transaction.objects.filter(account=self.account, description="Balance Adjustment").count(),
            2,
        )
