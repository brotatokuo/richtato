"""Tests for sync services."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.sync.models import SyncConnection
from apps.sync.services.teller_sync_service import TellerSyncService
from apps.transaction.models import Transaction, TransactionCategory
from django.test import TestCase


class TellerSyncServiceCategorizationTest(TestCase):
    """Tests for transaction categorization during sync."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.account = FinancialAccount.objects.create(
            user=self.user,
            name="Test Checking",
            account_type="checking",
            balance=Decimal("1000.00"),
        )
        self.sync_service = TellerSyncService()

    def test_ensure_user_categories_exist_creates_categories(self):
        """Test that categories are auto-created for users without categories."""
        # User should start with no categories
        self.assertEqual(TransactionCategory.objects.filter(user=self.user).count(), 0)

        # Call the method
        self.sync_service._ensure_user_categories_exist(self.user)

        # User should now have categories
        cat_count = TransactionCategory.objects.filter(user=self.user).count()
        self.assertGreater(cat_count, 0)
        print(f"Created {cat_count} categories for user")

        # Check that key categories exist
        category_names = list(
            TransactionCategory.objects.filter(user=self.user).values_list(
                "name", flat=True
            )
        )
        self.assertIn("Salary", category_names)
        self.assertIn("Groceries", category_names)
        self.assertIn("Dining", category_names)
        self.assertIn("Credit Card Payment", category_names)
        print(f"Categories created: {category_names[:10]}...")

    def test_ensure_user_categories_exist_does_not_duplicate(self):
        """Test that categories are not duplicated if they already exist."""
        # Create initial categories
        self.sync_service._ensure_user_categories_exist(self.user)
        initial_count = TransactionCategory.objects.filter(user=self.user).count()

        # Call again
        self.sync_service._ensure_user_categories_exist(self.user)
        final_count = TransactionCategory.objects.filter(user=self.user).count()

        self.assertEqual(initial_count, final_count)

    def test_keyword_category_map_includes_income_and_expense(self):
        """Test that keyword map includes both income and expense categories."""
        keyword_map = self.sync_service._get_keyword_category_map(self.user)

        # Should have keywords
        self.assertGreater(len(keyword_map), 0)
        print(f"Keyword map has {len(keyword_map)} entries")

        # Check some specific keywords
        # Income keywords
        self.assertIn("payroll", keyword_map)
        self.assertIn("salary", keyword_map)

        # Expense keywords
        self.assertIn("starbucks", keyword_map)
        self.assertIn("amazon", keyword_map)

        # Verify category types
        payroll_cat = keyword_map.get("payroll")
        self.assertTrue(payroll_cat.is_income)
        self.assertFalse(payroll_cat.is_expense)

        starbucks_cat = keyword_map.get("starbucks")
        self.assertFalse(starbucks_cat.is_income)
        self.assertTrue(starbucks_cat.is_expense)

    def test_categorize_by_keywords_matches_salary(self):
        """Test that salary/payroll transactions are categorized as income."""
        # Create categories first
        self.sync_service._ensure_user_categories_exist(self.user)

        # Create a transaction
        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            date="2024-01-15",
            amount=Decimal("3000.00"),
            description="GUSTO PAYROLL DEPOSIT",
            transaction_type="credit",
        )

        # Try to categorize
        category = self.sync_service._categorize_by_keywords(
            transaction, transaction.description, self.user
        )

        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Salary")
        self.assertTrue(category.is_income)
        print(f"Matched '{transaction.description}' to category: {category.name}")

    def test_categorize_by_keywords_matches_dining(self):
        """Test that restaurant transactions are categorized as dining."""
        self.sync_service._ensure_user_categories_exist(self.user)

        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            date="2024-01-15",
            amount=Decimal("25.00"),
            description="STARBUCKS STORE #12345",
            transaction_type="debit",
        )

        category = self.sync_service._categorize_by_keywords(
            transaction, transaction.description, self.user
        )

        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Dining")
        print(f"Matched '{transaction.description}' to category: {category.name}")

    def test_categorize_by_keywords_matches_groceries(self):
        """Test that grocery store transactions are categorized correctly."""
        self.sync_service._ensure_user_categories_exist(self.user)

        # Use "TRADER JOE'S" which has "trader joe's" as keyword for Groceries
        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            date="2024-01-15",
            amount=Decimal("150.00"),
            description="TRADER JOE'S STORE #123",
            transaction_type="debit",
        )

        category = self.sync_service._categorize_by_keywords(
            transaction, transaction.description, self.user
        )

        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Groceries")
        print(f"Matched '{transaction.description}' to category: {category.name}")

    def test_categorize_by_keywords_no_match_returns_none(self):
        """Test that unknown descriptions return None."""
        self.sync_service._ensure_user_categories_exist(self.user)

        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            date="2024-01-15",
            amount=Decimal("50.00"),
            description="RANDOM MERCHANT XYZ123",
            transaction_type="debit",
        )

        category = self.sync_service._categorize_by_keywords(
            transaction, transaction.description, self.user
        )

        self.assertIsNone(category)
        print(f"No match for '{transaction.description}' (expected)")

    def test_auto_categorize_transaction_cc_payment(self):
        """Test that credit card payments are auto-categorized."""
        self.sync_service._ensure_user_categories_exist(self.user)

        # Create a credit card account
        cc_account = FinancialAccount.objects.create(
            user=self.user,
            name="Test Credit Card",
            account_type="credit_card",
            balance=Decimal("500.00"),
            is_liability=True,
        )

        transaction = Transaction.objects.create(
            user=self.user,
            account=cc_account,
            date="2024-01-15",
            amount=Decimal("500.00"),
            description="PAYMENT THANK YOU",
            transaction_type="credit",
        )

        result = self.sync_service._auto_categorize_transaction(
            transaction, nature_hint="cc_payment"
        )

        self.assertTrue(result)
        transaction.refresh_from_db()
        self.assertIsNotNone(transaction.category)
        self.assertEqual(transaction.category.name, "Credit Card Payment")
        self.assertEqual(transaction.categorization_status, "categorized")
        print(f"CC payment categorized as: {transaction.category.name}")

    def test_auto_categorize_full_flow(self):
        """Test full auto-categorization flow with different transaction types."""
        self.sync_service._ensure_user_categories_exist(self.user)

        test_cases = [
            ("ADP PAYROLL DEPOSIT", "credit", "Salary", True),
            ("STARBUCKS COFFEE", "debit", "Dining", True),
            ("COSTCO WHOLESALE", "debit", "Wholesale", True),
            ("RANDOM UNKNOWN MERCHANT", "debit", None, False),
        ]

        for desc, txn_type, expected_cat, should_match in test_cases:
            transaction = Transaction.objects.create(
                user=self.user,
                account=self.account,
                date="2024-01-15",
                amount=Decimal("100.00"),
                description=desc,
                transaction_type=txn_type,
            )

            result = self.sync_service._auto_categorize_transaction(transaction)

            if should_match:
                self.assertTrue(result, f"Expected match for '{desc}'")
                transaction.refresh_from_db()
                self.assertEqual(
                    transaction.category.name,
                    expected_cat,
                    f"Wrong category for '{desc}'",
                )
                print(f"✓ '{desc}' → {transaction.category.name}")
            else:
                self.assertFalse(result, f"Expected no match for '{desc}'")
                transaction.refresh_from_db()
                self.assertIsNone(transaction.category)
                print(f"✓ '{desc}' → uncategorized (expected)")
