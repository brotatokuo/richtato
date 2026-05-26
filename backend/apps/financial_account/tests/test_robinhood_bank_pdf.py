"""Tests for Robinhood Banking (checking/savings) PDF statement parsing."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from apps.financial_account.institutions.parsers.robinhood_bank_pdf import (
    parse_robinhood_bank_balance_summary,
    parse_robinhood_bank_pdf,
)
from apps.financial_account.institutions.registry import supported_extensions_for_parser
from apps.financial_account.models import FinancialAccount, FinancialInstitution
from apps.financial_account.services.account_service import AccountService
from apps.financial_account.services.statement_import_service import (
    OPENING_BALANCE_DESCRIPTION,
    StatementImportService,
)
from apps.richtato_user.models import User
from apps.transaction.models import Transaction

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

    def test_parse_fixture_captures_running_balance_column(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_robinhood_bank_pdf(content)

        assert frame.iloc[0]["Balance"] == "4503.45"
        assert frame.iloc[-1]["Balance"] == "4331.39"


class TestRobinhoodBankBalanceSummary:
    def test_extract_balance_summary_from_april_fixture(self):
        content = FIXTURE_PATH.read_bytes()
        summary = parse_robinhood_bank_balance_summary(content)

        assert summary == {
            "beginning_balance": "3003.45",
            "ending_balance": "4331.39",
            "beginning_date": "2026-04-01",
            "ending_date": "2026-04-30",
        }


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

        assert result.balance_summary == {
            "beginning_balance": "3003.45",
            "ending_balance": "4331.39",
            "beginning_date": "2026-04-01",
            "ending_date": "2026-04-30",
        }
        assert result.reconciliation["statement_internal_ok"] is True
        assert result.reconciliation_warnings == []
        assert result.reconciliation["opening_balance_action"] == "available_create"

    def test_import_with_opening_balance_reconciles_ending_balance(self, robinhood_checking_account):
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "robinhood_checking_april_2026.pdf"

        result = service.import_statement(
            robinhood_checking_account,
            statement,
            "robinhood_bank",
            "2026-04",
            apply_opening_balance=True,
        )

        assert result.errors == []
        assert result.imported_count == 6
        assert result.reconciliation["opening_balance_applied"] is True
        assert result.reconciliation["opening_balance_action"] == "create"
        assert result.reconciliation["account_ending_ok"] is True

        opening_balance = Transaction.objects.get(
            account=robinhood_checking_account,
            description=OPENING_BALANCE_DESCRIPTION,
        )
        assert opening_balance.amount == Decimal("3003.45")
        assert opening_balance.date.isoformat() == "2026-04-01"

    def test_preview_offers_opening_balance_update_when_account_differs(self, robinhood_checking_account):
        AccountService().upsert_opening_balance(
            robinhood_checking_account,
            Decimal("500.00"),
            date(2026, 1, 1),
        )
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "robinhood_checking_april_2026.pdf"

        result = service.preview_statement(
            robinhood_checking_account,
            statement,
            "robinhood_bank",
            "2026-04",
        )

        assert result.reconciliation["opening_balance_action"] == "available_update"
        assert result.reconciliation["account_opening_balance_current"] == "500.00"

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
