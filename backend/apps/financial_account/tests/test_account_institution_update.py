"""Tests for updating account institution and type via PATCH."""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.financial_account.services.account_service import AccountService
from apps.richtato_user.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="acctupdate", email="acctupdate@test.com", password="x")


@pytest.fixture
def other_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="bank_of_america",
        defaults={"name": "Bank of America"},
    )
    return institution


@pytest.fixture
def guideline_institution(db):
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="guideline",
        defaults={"name": "Guideline"},
    )
    return institution


class TestAccountInstitutionUpdate:
    def test_patch_updates_institution_slug(self, user, other_institution, guideline_institution):
        account = FinancialAccount.objects.create(
            user=user,
            name="401(k)",
            account_type="investment",
            institution=other_institution,
            balance=Decimal("1000.00"),
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch(
            reverse("account-detail", kwargs={"pk": account.id}),
            {"institution_slug": "guideline", "account_type": "investment"},
            format="json",
        )

        assert response.status_code == 200
        account.refresh_from_db()
        assert account.institution.slug == "guideline"
        assert response.json()["entity"] == "guideline"
        assert response.json()["institution_name"] == "Guideline"

    def test_create_account_links_guideline_from_registry_when_missing_in_db(self, user):
        from apps.financial_account.models import FinancialInstitution

        FinancialInstitution.objects.filter(slug="guideline").delete()

        account = AccountService().create_manual_account(
            user=user,
            name="401(k)",
            account_type="investment",
            institution_slug="guideline",
        )

        assert account.institution is not None
        assert account.institution.slug == "guideline"
        assert account.institution.name == "Guideline"

    def test_patch_rejects_invalid_institution_type_pair(self, user, other_institution):
        account = FinancialAccount.objects.create(
            user=user,
            name="Checking",
            account_type="checking",
            institution=other_institution,
            balance=Decimal("100.00"),
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch(
            reverse("account-detail", kwargs={"pk": account.id}),
            {"institution_slug": "guideline", "account_type": "checking"},
            format="json",
        )

        assert response.status_code == 400
