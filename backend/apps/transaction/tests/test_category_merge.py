"""Tests for category merging in household scope."""

import pytest

from apps.richtato_user.models import User
from apps.transaction.models import TransactionCategory
from apps.transaction.repositories.category_repository import CategoryRepository


@pytest.fixture
def user_a(db):
    return User.objects.create_user(username="cat_a", password="testpass123")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(username="cat_b", password="testpass123")


@pytest.fixture
def repo():
    return CategoryRepository()


class TestCategoryMerge:
    def test_merges_categories_with_same_slug(self, repo, user_a, user_b):
        TransactionCategory.objects.create(user=user_a, name="Custom Shared", slug="custom-shared", type="expense")
        TransactionCategory.objects.create(user=user_b, name="Custom Shared", slug="custom-shared", type="expense")
        result = repo.get_merged_for_users([user_a.id, user_b.id])
        slugs = [c.slug for c in result]
        assert slugs.count("custom-shared") == 1

    def test_keeps_unique_categories_from_both_users(self, repo, user_a, user_b):
        TransactionCategory.objects.create(user=user_a, name="Exotic Pets", slug="exotic-pets", type="expense")
        TransactionCategory.objects.create(user=user_b, name="Board Games", slug="board-games", type="expense")
        result = repo.get_merged_for_users([user_a.id, user_b.id])
        slugs = {c.slug for c in result}
        assert "exotic-pets" in slugs
        assert "board-games" in slugs

    def test_canonical_metadata_uses_first_members_category(self, repo, user_a, user_b):
        TransactionCategory.objects.create(
            user=user_a, name="Hobby A", slug="test-hobby", type="expense", icon="apple",
        )
        TransactionCategory.objects.create(
            user=user_b, name="Hobby B", slug="test-hobby", type="expense", icon="cart",
        )
        result = repo.get_merged_for_users([user_a.id, user_b.id])
        hobby_cats = [c for c in result if c.slug == "test-hobby"]
        assert len(hobby_cats) == 1
        assert hobby_cats[0].user == user_a

    def test_no_merge_needed_for_personal_scope(self, repo, user_a):
        TransactionCategory.objects.create(user=user_a, name="Cat Only A", slug="cat-only-a", type="expense")
        TransactionCategory.objects.create(user=user_a, name="Cat Only B", slug="cat-only-b", type="expense")
        merged = repo.get_merged_for_users([user_a.id])
        slugs = {c.slug for c in merged}
        assert "cat-only-a" in slugs
        assert "cat-only-b" in slugs
