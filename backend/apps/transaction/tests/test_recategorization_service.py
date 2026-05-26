"""Tests for bulk recategorization performance and correctness."""

from datetime import date
from decimal import Decimal

import pytest

from apps.financial_account.models import FinancialAccount
from apps.richtato_user.models import User
from apps.transaction.models import CategoryKeyword, RecategorizationTask, Transaction, TransactionCategory
from apps.transaction.services.recategorization_service import RecategorizationService


@pytest.fixture
def user(db):
    return User.objects.create_user(username="recat", email="recat@test.com", password="testpass123")


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="Recat Account",
        account_type="checking",
        balance=Decimal("1000.00"),
    )


@pytest.fixture
def grocery_category(user):
    return TransactionCategory.objects.create(
        user=user,
        name="Groceries",
        slug="groceries-recat",
        type="expense",
    )


@pytest.fixture
def grocery_keyword(user, grocery_category):
    return CategoryKeyword.objects.create(
        user=user,
        category=grocery_category,
        keyword="xyzzy_recategorize_test",
    )


def _create_uncategorized_txn(user, account, description: str) -> Transaction:
    return Transaction.objects.create(
        user=user,
        account=account,
        date=date.today(),
        amount=Decimal("10.00"),
        transaction_type="debit",
        description=description,
        categorization_status="uncategorized",
    )


class TestRecategorizationService:
    def test_applies_keyword_matches_in_bulk(self, user, account, grocery_category, grocery_keyword):
        # User signup seeds hundreds of default keywords; isolate this test's rule.
        CategoryKeyword.objects.filter(user=user).exclude(pk=grocery_keyword.pk).delete()

        _create_uncategorized_txn(user, account, "XYZZY_RECATEGORIZE_TEST STORE")
        _create_uncategorized_txn(user, account, "XYZZY_RECATEGORIZE_TEST #2")

        task = RecategorizationTask.objects.create(user=user, keep_existing_for_unmatched=True)
        stats = RecategorizationService().recategorize_all_transactions(task)

        assert stats["updated"] == 2
        assert stats["unmatched"] == 0
        assert Transaction.objects.filter(user=user, categorization_status="categorized").count() == 2
        category_ids = set(Transaction.objects.filter(user=user).values_list("category_id", flat=True))
        assert category_ids == {grocery_category.id}, f"got category_ids={category_ids}"

        account.refresh_from_db()
        # Debits on create lowered balance; recategorization must not touch balances.
        assert account.balance == Decimal("980.00")

    def test_keep_existing_leaves_unmatched_unchanged(self, user, account, grocery_keyword):
        txn = _create_uncategorized_txn(user, account, "UNKNOWN MERCHANT")

        task = RecategorizationTask.objects.create(user=user, keep_existing_for_unmatched=True)
        stats = RecategorizationService().recategorize_all_transactions(task)

        assert stats["updated"] == 0
        assert stats["unmatched"] == 1
        txn.refresh_from_db()
        assert txn.categorization_status == "uncategorized"
