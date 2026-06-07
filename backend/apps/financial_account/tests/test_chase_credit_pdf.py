"""Tests for Chase credit card PDF statement parsing."""

from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

import pytest

from apps.financial_account.institutions.parsers.chase_credit_pdf import parse_chase_credit_pdf
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.financial_account.services.statement_import_service import StatementImportService
from apps.richtato_user.models import User

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "chase_credit_june_2026.pdf"


@pytest.fixture
def chase_credit_account(db):
    user = User.objects.create_user(username="chase-credit", email="chase-credit@test.com", password="x")
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="chase",
        defaults={"name": "Chase"},
    )
    return FinancialAccount.objects.create(
        user=user,
        name="Sapphire Reserve",
        account_type="credit_card",
        institution=institution,
        account_number_last4="9809",
    )


class TestChaseCreditPdfParser:
    def test_parse_fixture_extracts_expected_transaction_count(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_chase_credit_pdf(content)

        assert len(frame) == 36
        assert set(frame.columns) >= {"Transaction Date", "Description", "Amount", "Account Hint"}
        assert frame.iloc[0]["Account Hint"] == "9809"

    def test_parse_fixture_classifies_payments_and_purchases(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_chase_credit_pdf(content)

        payments = frame[frame["Description"].str.contains("Payment Thank You", na=False)]
        assert len(payments) == 2
        assert all(str(amount).startswith("-") for amount in payments["Amount"])


class TestChaseCreditPdfImport:
    def test_preview_chase_credit_pdf(self, chase_credit_account):
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "chase_credit_june_2026.pdf"

        result = service.preview_statement(
            chase_credit_account,
            statement,
            "chase_credit",
            "2026-06",
        )

        assert result.errors == []
        assert result.parsed_count == 36
        assert result.institution == "chase_credit"

        purchases = [row for row in result.rows if row.transaction_type == "debit"]
        credits = [row for row in result.rows if row.transaction_type == "credit"]
        assert len(purchases) == 34
        assert len(credits) == 2

        payment = next(row for row in result.rows if "Payment Thank You-Mobile" in row.description)
        assert payment.transaction_type == "credit"
        assert payment.amount == Decimal("813.65")

        purchase = next(row for row in result.rows if row.description == "KUNJIP SANTA CLARA CA")
        assert purchase.transaction_type == "debit"
        assert purchase.amount == Decimal("34.07")
        assert purchase.posted_date.isoformat() == "2026-05-05"

    def test_rejects_non_chase_pdf(self, chase_credit_account):
        service = StatementImportService()
        statement = io.BytesIO(b"%PDF-1.4\n% not a chase statement")
        statement.name = "other.pdf"

        result = service.preview_statement(
            chase_credit_account,
            statement,
            "chase_credit",
            "2026-06",
        )

        assert result.parsed_count == 0
        assert result.errors
        assert any("parse" in error.lower() for error in result.errors)
