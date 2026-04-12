"""API integration tests for budget views."""

from datetime import date, timedelta
from decimal import Decimal

from apps.budget.models import Budget, BudgetCategory
from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import Transaction, TransactionCategory
from django.test import TestCase
from rest_framework.test import APIClient


class BudgetAPITestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="apitest", email="api@test.com", password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.account = FinancialAccount.objects.create(
            user=self.user, name="Checking", account_type="checking",
            balance=Decimal("10000.00"),
        )
        self.category = TransactionCategory.objects.create(
            user=self.user, name="API Groceries", slug="api-groceries-test", type="expense",
        )
        self.category_2 = TransactionCategory.objects.create(
            user=self.user, name="API Transport", slug="api-transport-test", type="expense",
        )


class TestBudgetListCreateAPI(BudgetAPITestBase):
    def test_list_returns_active_budgets(self):
        Budget.objects.create(
            user=self.user, name="Active", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        Budget.objects.create(
            user=self.user, name="Inactive", period_type="monthly",
            start_date=date(2024, 2, 1), end_date=date(2024, 2, 29), is_active=False,
        )
        response = self.client.get("/api/v1/budgets/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["budgets"]), 1)
        self.assertEqual(data["budgets"][0]["name"], "Active")

    def test_list_with_active_only_false(self):
        Budget.objects.create(
            user=self.user, name="Active", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        Budget.objects.create(
            user=self.user, name="Inactive", period_type="monthly",
            start_date=date(2024, 2, 1), end_date=date(2024, 2, 29), is_active=False,
        )
        response = self.client.get("/api/v1/budgets/?active_only=false")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["budgets"]), 2)

    def test_create_budget_without_categories(self):
        response = self.client.post("/api/v1/budgets/", {
            "name": "March 2024",
            "period_type": "monthly",
            "start_date": "2024-03-01",
            "end_date": "2024-03-31",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "March 2024")
        self.assertEqual(data["period_type"], "monthly")

    def test_create_budget_with_categories_fails_due_to_kwarg_mismatch(self):
        """Documents known bug: serializer uses 'categories' but service expects 'categories_data'."""
        response = self.client.post("/api/v1/budgets/", {
            "name": "With Cats",
            "period_type": "monthly",
            "start_date": "2024-03-01",
            "end_date": "2024-03-31",
            "categories": [
                {"category_id": self.category.id, "allocated_amount": "300.00"},
            ],
        }, format="json")
        self.assertEqual(response.status_code, 500)

    def test_create_budget_validation_error(self):
        response = self.client.post("/api/v1/budgets/", {
            "name": "Bad",
            "period_type": "invalid_type",
            "start_date": "2024-03-01",
            "end_date": "2024-03-31",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_error(self):
        anon = APIClient()
        response = anon.get("/api/v1/budgets/")
        self.assertIn(response.status_code, [401, 403])


class TestBudgetDetailAPI(BudgetAPITestBase):
    def test_get_budget_detail(self):
        budget = Budget.objects.create(
            user=self.user, name="Detail Test", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        BudgetCategory.objects.create(
            budget=budget, category=self.category, allocated_amount=Decimal("500.00"),
        )
        response = self.client.get(f"/api/v1/budgets/{budget.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Detail Test")
        self.assertEqual(len(data["budget_categories"]), 1)

    def test_get_other_users_budget_returns_404(self):
        other = User.objects.create_user(
            username="other", email="o@test.com", password="testpass123",
        )
        budget = Budget.objects.create(
            user=other, name="Not Mine", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        response = self.client.get(f"/api/v1/budgets/{budget.id}/")
        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_returns_404(self):
        response = self.client.get("/api/v1/budgets/99999/")
        self.assertEqual(response.status_code, 404)

    def test_delete_soft_deletes(self):
        budget = Budget.objects.create(
            user=self.user, name="To Delete", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        response = self.client.delete(f"/api/v1/budgets/{budget.id}/")
        self.assertEqual(response.status_code, 204)
        budget.refresh_from_db()
        self.assertFalse(budget.is_active)

    def test_delete_nonexistent_returns_404(self):
        response = self.client.delete("/api/v1/budgets/99999/")
        self.assertEqual(response.status_code, 404)


class TestBudgetProgressAPI(BudgetAPITestBase):
    def test_progress_returns_correct_shape(self):
        budget = Budget.objects.create(
            user=self.user, name="Progress Test", period_type="monthly",
            start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
        )
        BudgetCategory.objects.create(
            budget=budget, category=self.category, allocated_amount=Decimal("500.00"),
        )
        Transaction.objects.create(
            user=self.user, account=self.account, category=self.category,
            amount=Decimal("150.00"), date=date(2024, 1, 10),
            description="Grocery run", transaction_type="debit", sync_source="manual",
        )

        response = self.client.get(f"/api/v1/budgets/{budget.id}/progress/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("budget_id", data)
        self.assertIn("totals", data)
        self.assertIn("categories", data)
        self.assertEqual(Decimal(str(data["totals"]["spent"])), Decimal("150.00"))
        self.assertEqual(len(data["categories"]), 1)

    def test_progress_nonexistent_returns_404(self):
        response = self.client.get("/api/v1/budgets/99999/progress/")
        self.assertEqual(response.status_code, 404)


class TestCurrentBudgetAPI(BudgetAPITestBase):
    def test_returns_current_budget_with_progress(self):
        today = date.today()
        budget = Budget.objects.create(
            user=self.user, name="Current", period_type="monthly",
            start_date=today - timedelta(days=15),
            end_date=today + timedelta(days=15),
        )
        BudgetCategory.objects.create(
            budget=budget, category=self.category, allocated_amount=Decimal("1000.00"),
        )
        response = self.client.get("/api/v1/budgets/current/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("budget", data)
        self.assertIn("progress", data)
        self.assertEqual(data["budget"]["name"], "Current")

    def test_returns_404_when_no_current(self):
        Budget.objects.create(
            user=self.user, name="Past", period_type="monthly",
            start_date=date(2020, 1, 1), end_date=date(2020, 1, 31),
        )
        response = self.client.get("/api/v1/budgets/current/")
        self.assertEqual(response.status_code, 404)
