"""Tests for account repository household scope queries."""

from decimal import Decimal

import pytest

from apps.financial_account.models import FinancialAccount
from apps.financial_account.repositories.account_repository import FinancialAccountRepository
from apps.household.models import Household, HouseholdMember
from apps.richtato_user.models import User


@pytest.fixture
def user_a(db):
    return User.objects.create_user(username="acct_a", password="testpass123")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(username="acct_b", password="testpass123")


@pytest.fixture
def household_both(user_a, user_b):
    h = Household.objects.create(name="Test", created_by=user_a)
    HouseholdMember.objects.create(household=h, user=user_a)
    HouseholdMember.objects.create(household=h, user=user_b)
    return h


@pytest.fixture
def shared_a(user_a):
    return FinancialAccount.objects.create(
        user=user_a, name="A Shared", account_type="checking",
        balance=Decimal("1000"), shared_with_household=True,
    )


@pytest.fixture
def private_a(user_a):
    return FinancialAccount.objects.create(
        user=user_a, name="A Private", account_type="savings",
        balance=Decimal("2000"), shared_with_household=False,
    )


@pytest.fixture
def shared_b(user_b):
    return FinancialAccount.objects.create(
        user=user_b, name="B Shared", account_type="checking",
        balance=Decimal("3000"), shared_with_household=True,
    )


@pytest.fixture
def private_b(user_b):
    return FinancialAccount.objects.create(
        user=user_b, name="B Private", account_type="savings",
        balance=Decimal("500"), shared_with_household=False,
    )


@pytest.fixture
def repo():
    return FinancialAccountRepository()


class TestHouseholdScopeAccounts:
    def test_personal_scope_returns_only_own_accounts(self, repo, user_a, shared_a, private_a, shared_b):
        result = repo.get_by_user(user_a)
        ids = {a.id for a in result}
        assert shared_a.id in ids
        assert private_a.id in ids
        assert shared_b.id not in ids

    def test_household_scope_returns_shared_accounts_from_all_members(
        self, repo, user_a, user_b, household_both, shared_a, shared_b,
    ):
        user_ids = [user_a.id, user_b.id]
        result = repo.get_by_user_ids_shared(user_ids)
        ids = {a.id for a in result}
        assert shared_a.id in ids
        assert shared_b.id in ids

    def test_household_scope_excludes_unshared_accounts(
        self, repo, user_a, user_b, household_both, shared_a, private_b,
    ):
        user_ids = [user_a.id, user_b.id]
        result = repo.get_by_user_ids_shared(user_ids)
        ids = {a.id for a in result}
        assert private_b.id not in ids

    def test_household_scope_with_no_household_returns_own_accounts(self, repo, user_a, shared_a):
        result = repo.get_by_user_ids_shared([user_a.id])
        ids = {a.id for a in result}
        assert shared_a.id in ids

    def test_shared_flag_toggle(self, repo, user_a, user_b, household_both, private_a):
        user_ids = [user_a.id, user_b.id]
        result = repo.get_by_user_ids_shared(user_ids)
        assert private_a.id not in {a.id for a in result}

        private_a.shared_with_household = True
        private_a.save()

        result = repo.get_by_user_ids_shared(user_ids)
        assert private_a.id in {a.id for a in result}
