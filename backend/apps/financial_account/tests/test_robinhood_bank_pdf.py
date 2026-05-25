"""Tests for Robinhood Banking (checking/savings) PDF statement parsing."""

from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

import pytest

from apps.financial_account.institutions.parsers.robinhood_bank_pdf import parse_robinhood_bank_pdf
from apps.financial_account.institutions.registry import supported_extensions_for_parser
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.financial_account.services.statement_import_service import StatementImportService
from apps.richtato_user.models import User

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "robinhood_checking_april_2026.pdf"


@pytest.fixture
def robinhood_checking_account(db):
    user = User.objects.create_user(username="robinhood-checking", email="rh-checking@test.com", password="x")
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="robinhood",
        defaults={"name": "Robinhood"},
    )
    return FinancialAccount.objects.create(
        user=user,
        name="Joint Checking",
        account_type="checking",
        institution=institution,
    )


class TestRobinhoodBankPdfParser:
    def test_parse_fixture_extracts_expected_transaction_count(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_robinhood_bank_pdf(content)

        assert len(frame) == 6
        assert set(frame.columns) >= {"Date", "Description", "Amount"}

    def test_parse_fixture_handles_split_descriptions(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_robinhood_bank_pdf(content)

        transfer = frame[frame["Description"].str.contains("Gold Card", na=False)]
        assert len(transfer) == 3
        assert transfer.iloc[0]["Description"] == "Inter-Entity Transfer to Robinhood Gold Card"


class TestRobinhoodBankPdfImport:
    def test_preview_robinhood_checking_pdf(self, robinhood_checking_account):
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "robinhood_checking_april_2026.pdf"

        result = service.preview_statement(
            robinhood_checking_account,
            statement,
            "robinhood_bank",
            "2026-04",
        )

        assert result.errors == []
        assert result.parsed_count == 6
        assert result.institution == "robinhood_bank"

        deposits = [row for row in result.rows if row.transaction_type == "credit"]
        withdrawals = [row for row in result.rows if row.transaction_type == "debit"]
        assert len(deposits) == 3
        assert len(withdrawals) == 3

        ach_deposit = next(row for row in result.rows if "ACH Deposit" in row.description)
        assert ach_deposit.transaction_type == "credit"
        assert ach_deposit.amount == Decimal("1500.00")

        transfer = next(row for row in result.rows if "Gold Card" in row.description)
        assert transfer.transaction_type == "debit"
        assert transfer.amount == Decimal("617.91")

        interest = next(row for row in result.rows if row.description == "Interest Payment")
        assert interest.transaction_type == "credit"
        assert interest.amount == Decimal("10.20")

    def test_rejects_non_robinhood_bank_pdf(self, robinhood_checking_account):
        service = StatementImportService()
        statement = io.BytesIO(b"%PDF-1.4\n% not a robinhood statement")
        statement.name = "other.pdf"

        result = service.preview_statement(
            robinhood_checking_account,
            statement,
            "robinhood_bank",
            "2026-04",
        )

        assert result.parsed_count == 0
        assert result.errors
        assert any("parse" in error.lower() for error in result.errors)


def test_supported_extensions_for_robinhood_bank_includes_pdf():
    extensions = supported_extensions_for_parser("robinhood_bank")
    assert ".pdf" in extensions
    assert ".csv" in extensions
