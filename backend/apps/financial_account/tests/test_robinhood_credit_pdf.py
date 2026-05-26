"""Tests for Robinhood Credit Card PDF statement parsing."""

from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

import pytest

from apps.financial_account.institutions.parsers.robinhood_credit_pdf import parse_robinhood_credit_pdf
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.financial_account.services.statement_import_service import StatementImportService
from apps.richtato_user.models import User

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "robinhood_credit_may_2026.pdf"


@pytest.fixture
def robinhood_credit_account(db):
    user = User.objects.create_user(username="robinhood-credit", email="rh-credit@test.com", password="x")
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="robinhood",
        defaults={"name": "Robinhood"},
    )
    return FinancialAccount.objects.create(
        user=user,
        name="Robinhood Gold Card",
        account_type="credit_card",
        institution=institution,
    )


class TestRobinhoodCreditPdfParser:
    def test_parse_fixture_extracts_expected_transaction_count(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_robinhood_credit_pdf(content)

        assert len(frame) == 25
        assert set(frame.columns) >= {"Post Date", "Transaction Description", "Amount", "Reference Number"}

    def test_parse_fixture_classifies_payments_and_refunds(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_robinhood_credit_pdf(content)

        payments = frame[frame["Transaction Description"].str.contains("PAYMENT", na=False)]
        assert len(payments) == 4
        assert all(str(amount).startswith("-") for amount in payments["Amount"])

        refunds = frame[frame["Transaction Description"].str.contains("OASIS", na=False)]
        assert len(refunds) == 1
        assert refunds.iloc[0]["Amount"] == "-508.20"


class TestRobinhoodCreditPdfImport:
    def test_preview_robinhood_credit_pdf(self, robinhood_credit_account):
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "robinhood_credit_may_2026.pdf"

        result = service.preview_statement(
            robinhood_credit_account,
            statement,
            "robinhood_credit",
            "2026-05",
        )

        assert result.errors == []
        assert result.parsed_count == 25
        assert result.institution == "robinhood_credit"

        purchases = [row for row in result.rows if row.transaction_type == "debit"]
        credits = [row for row in result.rows if row.transaction_type == "credit"]
        assert len(purchases) == 20
        assert len(credits) == 5

        payment = next(row for row in result.rows if "PAYMENT" in row.description)
        assert payment.transaction_type == "credit"
        assert payment.amount == Decimal("264.71")

        purchase = next(row for row in result.rows if row.description == "TAIWANRESTAURANTSANJOSE CA")
        assert purchase.transaction_type == "debit"
        assert purchase.amount == Decimal("84.58")
        assert purchase.posted_date.isoformat() == "2026-04-17"

    def test_rejects_non_robinhood_pdf(self, robinhood_credit_account):
        service = StatementImportService()
        statement = io.BytesIO(b"%PDF-1.4\n% not a robinhood statement")
        statement.name = "other.pdf"

        result = service.preview_statement(
            robinhood_credit_account,
            statement,
            "robinhood_credit",
            "2026-05",
        )

        assert result.parsed_count == 0
        assert result.errors
        assert any("parse" in error.lower() for error in result.errors)

    def test_rejects_pdf_for_csv_institution(self, robinhood_credit_account):
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "robinhood_credit_may_2026.pdf"

        result = service.preview_statement(
            robinhood_credit_account,
            statement,
            "chase",
            "2026-05",
        )

        assert result.parsed_count == 0
        assert any("Unsupported file type" in error for error in result.errors)
