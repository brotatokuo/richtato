"""Tests for American Express Rewards Checking PDF statement parsing."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from rest_framework.test import APIClient

from apps.financial_account.institutions.parsers.amex_checking_pdf import (
    parse_amex_checking_balance_summary,
    parse_amex_checking_pdf,
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

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "amex_checking_january_2026.pdf"


@pytest.fixture
def amex_checking_account(db):
    user = User.objects.create_user(username="amex-checking", email="amex-checking@test.com", password="x")
    institution, _ = FinancialInstitution.objects.get_or_create(
        slug="american_express",
        defaults={"name": "American Express"},
    )
    return FinancialAccount.objects.create(
        user=user,
        name="Rewards Checking",
        account_type="checking",
        institution=institution,
    )


class TestAmexCheckingPdfParser:
    def test_parse_fixture_extracts_expected_transaction_count(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_amex_checking_pdf(content)

        assert len(frame) == 29
        assert set(frame.columns) >= {"Date", "Description", "Amount", "Balance"}

    def test_parse_fixture_handles_multiline_descriptions(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_amex_checking_pdf(content)

        transfer = frame[frame["Description"].str.contains("American Express TRANSFER", na=False)]
        assert len(transfer) == 1
        assert "BANK OF AMERICA,N.A." in transfer.iloc[0]["Description"]
        assert "americanexpress.com" not in transfer.iloc[0]["Description"]

    def test_parse_fixture_captures_running_balance_column(self):
        content = FIXTURE_PATH.read_bytes()
        frame = parse_amex_checking_pdf(content)

        assert frame.iloc[0]["Balance"] == "8998.61"
        assert frame.iloc[-1]["Balance"] == "10280.56"

    def test_parse_split_rows_with_trailing_amount_balance(self, monkeypatch):
        sample_text = """
American Express Rewards Checking
Statement Date: 08/31/2024 Account Ending: *0118
Account Activity
Date Description Credits Debits Balance
08/09/2024 Online Transfer / Payment: Credit
LG ENERGY SOLUTI DIRECT DEP *****0019
$2,308.26 $7,259.65
08/27/2024 Online Transfer / Payment: Debit
AMEX EPAYMENT ACH PMT *****0019
($185.97) $7,073.68
08/31/2024 Ending Balance $7,073.68
""".strip()
        monkeypatch.setattr(
            "apps.financial_account.institutions.parsers.amex_checking_pdf._extract_pdf_text",
            lambda _content: sample_text,
        )

        frame = parse_amex_checking_pdf(b"%PDF-1.4")

        assert len(frame) == 2
        assert frame.iloc[0]["Amount"] == "2308.26"
        assert frame.iloc[0]["Balance"] == "7259.65"
        assert frame.iloc[1]["Amount"] == "(185.97)"
        assert frame.iloc[1]["Balance"] == "7073.68"

    def test_parse_inline_parenthesized_debits_with_continuation(self, monkeypatch):
        sample_text = """
American Express Rewards Checking
Statement Date: 05/31/2025 Account Ending: *0118
Account Activity
Date Description Credits Debits Balance
05/01/2025 Beginning Balance $4,259.75
05/01/2025 Online Transfer / Payment: Debit ($69.37) $4,190.38
CITI CARD ONLINE PAYMENT *****9681
ID 009002315550209
05/02/2025 Online Transfer / Payment: Credit $2,849.90 $6,940.01
GUSTO PAY 516812 *****0021
ID 009002315986217
05/31/2025 Ending Balance $6,940.01
""".strip()
        monkeypatch.setattr(
            "apps.financial_account.institutions.parsers.amex_checking_pdf._extract_pdf_text",
            lambda _content: sample_text,
        )

        frame = parse_amex_checking_pdf(b"%PDF-1.4")

        assert len(frame) == 2
        assert frame.iloc[0]["Amount"] == "(69.37)"
        assert frame.iloc[0]["Balance"] == "4190.38"
        assert "CITI CARD ONLINE PAYMENT" in frame.iloc[0]["Description"]
        assert frame.iloc[1]["Amount"] == "2849.90"


class TestAmexCheckingBalanceSummary:
    def test_extract_balance_summary_from_january_fixture(self):
        content = FIXTURE_PATH.read_bytes()
        summary = parse_amex_checking_balance_summary(content)

        assert summary == {
            "beginning_balance": "9005.23",
            "ending_balance": "10280.56",
            "beginning_date": "2026-01-01",
            "ending_date": "2026-01-31",
        }


class TestAmexCheckingPdfImport:
    def test_preview_amex_checking_pdf(self, amex_checking_account):
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "amex_checking_january_2026.pdf"

        result = service.preview_statement(
            amex_checking_account,
            statement,
            "amex_checking",
            "2026-01",
        )

        assert result.errors == []
        assert result.parsed_count == 29
        assert result.institution == "amex_checking"

        deposits = [row for row in result.rows if row.transaction_type == "credit"]
        withdrawals = [row for row in result.rows if row.transaction_type == "debit"]
        assert len(deposits) == 14
        assert len(withdrawals) == 15

        payroll = next(row for row in result.rows if "GUSTO PAY" in row.description)
        assert payroll.transaction_type == "credit"
        assert payroll.amount == Decimal("4012.45")
        assert payroll.running_balance

        interest = next(row for row in result.rows if row.description.startswith("Interest Deposit"))
        assert interest.transaction_type == "credit"
        assert interest.amount == Decimal("4.03")
        assert interest.running_balance == "10280.56"

        assert result.balance_summary == {
            "beginning_balance": "9005.23",
            "ending_balance": "10280.56",
            "beginning_date": "2026-01-01",
            "ending_date": "2026-01-31",
        }
        assert result.reconciliation["statement_internal_ok"] is True
        assert result.reconciliation_warnings == []
        assert result.reconciliation["opening_balance_action"] == "available_create"

    def test_import_with_opening_balance_reconciles_ending_balance(self, amex_checking_account):
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "amex_checking_january_2026.pdf"

        result = service.import_statement(
            amex_checking_account,
            statement,
            "amex_checking",
            "2026-01",
            apply_opening_balance=True,
        )

        assert result.errors == []
        assert result.imported_count == 29
        assert result.reconciliation["opening_balance_applied"] is True
        assert result.reconciliation["opening_balance_action"] == "create"
        assert result.reconciliation["account_ending_ok"] is True

        opening_balance = Transaction.objects.get(
            account=amex_checking_account,
            description=OPENING_BALANCE_DESCRIPTION,
        )
        assert opening_balance.amount == Decimal("9005.23")
        assert opening_balance.date.isoformat() == "2026-01-01"

        imported_interest = Transaction.objects.get(
            account=amex_checking_account,
            description__startswith="Interest Deposit",
        )
        assert imported_interest.raw_data["running_balance"] == "10280.56"

    def test_preview_offers_opening_balance_update_when_account_differs(self, amex_checking_account):
        AccountService().upsert_opening_balance(
            amex_checking_account,
            Decimal("500.00"),
            date(2026, 1, 1),
        )
        service = StatementImportService()
        statement = io.BytesIO(FIXTURE_PATH.read_bytes())
        statement.name = "amex_checking_january_2026.pdf"

        result = service.preview_statement(
            amex_checking_account,
            statement,
            "amex_checking",
            "2026-01",
        )

        assert result.reconciliation["opening_balance_action"] == "available_update"
        assert result.reconciliation["account_opening_balance_current"] == "500.00"

    def test_rejects_non_amex_checking_pdf(self, amex_checking_account):
        service = StatementImportService()
        statement = io.BytesIO(b"%PDF-1.4\n% not an amex checking statement")
        statement.name = "other.pdf"

        result = service.preview_statement(
            amex_checking_account,
            statement,
            "amex_checking",
            "2026-01",
        )

        assert result.parsed_count == 0
        assert result.errors
        assert any("parse" in error.lower() for error in result.errors)


def test_supported_extensions_for_amex_checking_is_pdf_only():
    extensions = supported_extensions_for_parser("amex_checking")
    assert extensions == {".pdf"}


@pytest.mark.django_db
def test_transactions_api_returns_computed_and_statement_running_balances(amex_checking_account):
    user = amex_checking_account.user
    Transaction.objects.create(
        user=user,
        account=amex_checking_account,
        date=date(2026, 1, 1),
        amount=Decimal("1000.00"),
        transaction_type="credit",
        description=OPENING_BALANCE_DESCRIPTION,
        sync_source="manual",
        status="reconciled",
    )
    Transaction.objects.create(
        user=user,
        account=amex_checking_account,
        date=date(2026, 1, 2),
        amount=Decimal("120.00"),
        transaction_type="debit",
        description="Imported debit",
        sync_source="csv",
        status="posted",
        raw_data={"running_balance": "880.00"},
    )
    Transaction.objects.create(
        user=user,
        account=amex_checking_account,
        date=date(2026, 1, 3),
        amount=Decimal("50.00"),
        transaction_type="debit",
        description="Manual debit",
        sync_source="manual",
        status="posted",
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(f"/api/v1/transactions/?account_id={amex_checking_account.id}&page_size=100")
    assert response.status_code == 200

    payload = response.json()["transactions"]
    by_description = {row["description"]: row for row in payload}
    assert by_description[OPENING_BALANCE_DESCRIPTION]["computed_running_balance"] == "1000.00"
    assert by_description["Imported debit"]["computed_running_balance"] == "880.00"
    assert by_description["Imported debit"]["statement_running_balance"] == "880.00"
    assert by_description["Imported debit"]["running_balance_diff"] == "0.00"
    assert by_description["Manual debit"]["computed_running_balance"] == "830.00"
    assert by_description["Manual debit"]["statement_running_balance"] is None
    assert by_description["Manual debit"]["running_balance_diff"] is None
