"""Tests for the supported institution registry."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.financial_account.institutions.registry import (
    agent_flow_for_account,
    get_agent_institution_slug,
    get_institution_field_choices,
    get_supported_institutions,
    is_valid_account_type,
    parser_key_for_account,
    parser_key_for_slug,
    supported_extensions_for_parser,
    supported_file_types_for_parser,
)
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.financial_account.serializers import FinancialAccountCreateSerializer
from apps.richtato_user.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="registry-api", email="registry-api@test.com", password="x")


@pytest.mark.parametrize(
    ("slug", "expected_parser"),
    [
        ("bank_of_america", "bofa"),
        ("bofa", "bofa"),
        ("american_express", "amex"),
        ("citibank", "citi"),
        ("robinhood", "robinhood_bank"),
        ("robinhood_investments", "robinhood_bank"),
        ("guideline", "guideline"),
        ("other", None),
    ],
)
def test_parser_key_for_slug(slug, expected_parser):
    assert parser_key_for_slug(slug) == expected_parser


@pytest.mark.parametrize(
    ("slug", "account_type", "expected"),
    [
        ("american_express", "credit_card", True),
        ("american_express", "checking", True),
        ("citibank", "savings", False),
        ("chase", "checking", True),
        ("fidelity", "investment", True),
        ("fidelity", "checking", False),
        ("robinhood", "credit_card", True),
        ("robinhood", "investment", True),
        ("robinhood", "checking", True),
        ("other", "investment", True),
    ],
)
def test_is_valid_account_type(slug, account_type, expected):
    assert is_valid_account_type(slug, account_type) is expected


def test_get_agent_institution_slug_supports_legacy_aliases():
    assert get_agent_institution_slug("bank_of_america") == "bofa"
    assert get_agent_institution_slug("jpmorgan_chase") == "chase"
    assert get_agent_institution_slug("guideline") == "guideline"
    assert get_agent_institution_slug("robinhood") == "robinhood"
    assert get_agent_institution_slug("marcus") == "marcus"
    assert get_agent_institution_slug("american_express") is None


def test_marcus_savings_uses_investment_balance_flow():
    assert agent_flow_for_account("marcus", "savings") == "investment_balance"


def test_get_supported_institutions_uses_account_types():
    institutions = get_supported_institutions()
    amex = next(item for item in institutions if item["slug"] == "american_express")

    assert amex["id"] == "amex"
    assert amex["account_types"] == ["checking", "credit_card"]
    assert "csv" in amex["file_types"]
    assert "pdf" in amex["file_types"]


def test_get_institution_field_choices_includes_per_institution_types():
    payload = get_institution_field_choices()

    amex = next(item for item in payload["institutions"] if item["value"] == "american_express")
    assert {item["value"] for item in amex["account_types"]} == {"checking", "credit_card"}

    chase = next(item for item in payload["institutions"] if item["value"] == "chase")
    assert {item["value"] for item in chase["account_types"]} == {
        "checking",
        "savings",
        "credit_card",
    }

    robinhood = next(item for item in payload["institutions"] if item["value"] == "robinhood")
    assert {item["value"] for item in robinhood["account_types"]} == {
        "checking",
        "savings",
        "credit_card",
        "investment",
    }

    assert "robinhood_investments" not in {item["value"] for item in payload["institutions"]}

    assert payload["entity"][-1]["value"] == "other"


@pytest.mark.django_db
def test_parser_key_for_account_resolves_american_express():
    user = User.objects.create_user(username="registry", email="registry@test.com", password="x")
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="american_express",
        defaults={"name": "American Express"},
    )
    account = FinancialAccount.objects.create(
        user=user,
        name="Platinum",
        account_type="credit_card",
        institution=institution,
    )

    assert parser_key_for_account(account) == "amex"


@pytest.mark.django_db
def test_parser_key_for_account_routes_amex_checking():
    user = User.objects.create_user(username="amex-checking-registry", email="amex-ch@test.com", password="x")
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="american_express",
        defaults={"name": "American Express"},
    )
    checking_account = FinancialAccount.objects.create(
        user=user,
        name="Rewards Checking",
        account_type="checking",
        institution=institution,
    )

    assert parser_key_for_account(checking_account) == "amex_checking"


@pytest.mark.django_db
def test_parser_key_for_account_routes_robinhood_credit_card():
    user = User.objects.create_user(username="robinhood-registry", email="rh@test.com", password="x")
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="robinhood",
        defaults={"name": "Robinhood"},
    )
    credit_account = FinancialAccount.objects.create(
        user=user,
        name="Robinhood Card",
        account_type="credit_card",
        institution=institution,
    )
    checking_account = FinancialAccount.objects.create(
        user=user,
        name="Robinhood Checking",
        account_type="checking",
        institution=institution,
    )

    assert parser_key_for_account(credit_account) == "robinhood_credit"
    assert parser_key_for_account(checking_account) == "robinhood_bank"


@pytest.mark.django_db
def test_parser_key_for_account_routes_robinhood_investment():
    user = User.objects.create_user(username="robinhood-inv", email="rh-inv@test.com", password="x")
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="robinhood",
        defaults={"name": "Robinhood"},
    )
    investment_account = FinancialAccount.objects.create(
        user=user,
        name="Robinhood Brokerage",
        account_type="investment",
        institution=institution,
    )

    assert parser_key_for_account(investment_account) == "robinhood_investments"


def test_supported_file_types_for_robinhood_credit():
    assert supported_file_types_for_parser("robinhood_credit") == ["pdf"]
    assert supported_extensions_for_parser("robinhood_credit") == {".pdf"}
    assert ".pdf" not in supported_extensions_for_parser("chase")


def test_supported_file_types_for_robinhood_bank():
    bank_types = supported_file_types_for_parser("robinhood_bank")
    assert "pdf" in bank_types
    assert "csv" in bank_types
    assert supported_extensions_for_parser("robinhood_bank") == {".csv", ".pdf", ".xls", ".xlsx"}


def test_get_supported_institutions_includes_robinhood_credit_pdf():
    institutions = get_supported_institutions()
    robinhood_credit = next(item for item in institutions if item["id"] == "robinhood_credit")

    assert robinhood_credit["slug"] == "robinhood"
    assert robinhood_credit["account_types"] == ["credit_card"]
    assert robinhood_credit["file_types"] == ["pdf"]


def test_get_supported_institutions_includes_robinhood_investments():
    institutions = get_supported_institutions()
    robinhood_investments = next(item for item in institutions if item["id"] == "robinhood_investments")

    assert robinhood_investments["slug"] == "robinhood"
    assert robinhood_investments["account_types"] == ["investment"]
    assert robinhood_investments["file_types"] == ["csv", "xls", "xlsx"]


def test_get_supported_institutions_includes_amex_checking_pdf():
    institutions = get_supported_institutions()
    amex_checking = next(item for item in institutions if item["id"] == "amex_checking")

    assert amex_checking["slug"] == "american_express"
    assert amex_checking["account_types"] == ["checking"]
    assert amex_checking["file_types"] == ["pdf"]


def test_create_serializer_accepts_amex_checking():
    serializer = FinancialAccountCreateSerializer(
        data={
            "name": "Rewards Checking",
            "account_type": "checking",
            "institution_slug": "american_express",
        }
    )

    assert serializer.is_valid(), serializer.errors


def test_create_serializer_rejects_invalid_institution_type_pair():
    serializer = FinancialAccountCreateSerializer(
        data={
            "name": "Bad Combo",
            "account_type": "checking",
            "institution_slug": "citibank",
        }
    )

    assert not serializer.is_valid()
    assert "account_type" in serializer.errors


@pytest.mark.django_db
def test_account_field_choices_api(user):
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("account-field-choices"))

    assert response.status_code == 200
    payload = response.json()
    assert "institutions" in payload
    amex = next(item for item in payload["institutions"] if item["value"] == "american_express")
    assert {item["value"] for item in amex["account_types"]} == {"checking", "credit_card"}
