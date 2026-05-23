"""Shared fixtures for bank_sync tests."""

from decimal import Decimal

import pytest

from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.richtato_user.models import User


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice", password="testpass123")


@pytest.fixture
def bob(db):
    return User.objects.create_user(username="bob", password="testpass123")


@pytest.fixture
def runner_user(db):
    user = User.objects.create_user(
        username="automation_runner",
        password="testpass123",
    )
    user.is_automation_runner = True
    user.save(update_fields=["is_automation_runner"])
    return user


@pytest.fixture
def bofa_institution(db):
    # The 0001 data migration seeds 'bank_of_america' already; reuse it so we
    # exercise the same slug variant the agent will see in production.
    inst, _ = FinancialInstitution.objects.get_or_create(
        slug="bank_of_america",
        defaults={"name": "Bank of America"},
    )
    return inst


@pytest.fixture
def chase_institution(db):
    inst, _ = FinancialInstitution.objects.get_or_create(
        slug="chase",
        defaults={"name": "Chase"},
    )
    return inst


@pytest.fixture
def alice_checking(alice, bofa_institution):
    return FinancialAccount.objects.create(
        user=alice,
        name="Alice BoFA Checking",
        institution=bofa_institution,
        account_type="checking",
        balance=Decimal("1000.00"),
    )


@pytest.fixture
def alice_credit(alice, bofa_institution):
    return FinancialAccount.objects.create(
        user=alice,
        name="Alice BoFA Credit",
        institution=bofa_institution,
        account_type="credit_card",
        balance=Decimal("-250.00"),
        is_liability=True,
    )
