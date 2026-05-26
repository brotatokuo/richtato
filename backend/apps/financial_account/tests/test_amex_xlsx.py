"""Tests for American Express activity XLSX parsing."""

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from apps.financial_account.institutions.parsers.amex_xlsx import parse_amex_activity_excel
from apps.financial_account.services.statement_import_service import StatementImportService


def _make_amex_activity_xlsx(transactions: list[list[str]], name: str = "activity.xlsx") -> io.BytesIO:
    """Build an Amex activity export with the standard metadata preamble."""
    rows: list[list[str | None]] = [
        ["Transaction Details", "Blue Cash Preferred® / Apr 24, 2026 to May 24, 2026"],
        ["Prepared for"],
        ["CARD MEMBER"],
        ["Account Number"],
        ["XXXX-XXXXXX-31017"],
        [None],
        [
            "Date",
            "Description",
            "Amount",
            "Extended Details",
            "Appears On Your Statement As",
            "Address",
            "City/State",
            "Zip Code",
            "Country",
            "Reference",
            "Category",
        ],
        *transactions,
    ]
    buffer = io.BytesIO()
    pd.DataFrame(rows).to_excel(buffer, index=False, header=False, sheet_name="Transaction Details")
    buffer.seek(0)
    buffer.name = name
    return buffer


class TestAmexActivityParser:
    def test_parse_activity_export_skips_preamble(self):
        workbook = _make_amex_activity_xlsx(
            [
                [
                    "05/07/2026",
                    "APPLE.COM/BILL INTERNET CHARGE CA",
                    "9.99",
                    "Details",
                    "APPLE.COM/BILL INTERNET CHARGE CA",
                    "123 Main St",
                    "AUSTIN TX",
                    "78727",
                    "UNITED STATES",
                    "123456789",
                    "Merchandise & Supplies-Internet Purchase",
                ]
            ]
        )

        frame = parse_amex_activity_excel(workbook.getvalue())

        assert list(frame.columns[:3]) == ["Date", "Description", "Amount"]
        assert len(frame) == 1
        assert frame.iloc[0]["Date"] == "05/07/2026"
        assert frame.iloc[0]["Description"] == "APPLE.COM/BILL INTERNET CHARGE CA"
        assert frame.iloc[0]["Amount"] == "9.99"

    def test_parse_plain_table_without_preamble(self):
        buffer = io.BytesIO()
        pd.DataFrame(
            [
                {"Date": "2025-06-01", "Description": "Restaurant", "Amount": "42.12"},
            ]
        ).to_excel(buffer, index=False)
        buffer.seek(0)

        frame = parse_amex_activity_excel(buffer.getvalue())

        assert len(frame) == 1
        assert frame.iloc[0]["Description"] == "Restaurant"


class TestAmexStatementImport:
    @pytest.fixture
    def credit_card_account(self, db):
        from apps.financial_account.models import FinancialAccount
        from apps.richtato_user.models import User

        user = User.objects.create_user(username="amexuser", email="amex@test.com", password="testpass123")
        return FinancialAccount.objects.create(
            user=user,
            name="Amex Test Card",
            account_type="credit_card",
            balance=Decimal("-100.00"),
            is_liability=True,
        )

    def test_preview_amex_activity_export(self, credit_card_account):
        service = StatementImportService()
        statement = _make_amex_activity_xlsx(
            [
                [
                    "05/07/2026",
                    "APPLE.COM/BILL INTERNET CHARGE CA",
                    "9.99",
                    "",
                    "APPLE.COM/BILL INTERNET CHARGE CA",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "Merchandise & Supplies-Internet Purchase",
                ],
                [
                    "05/01/2026",
                    "MOBILE PAYMENT - THANK YOU",
                    "-500.00",
                    "",
                    "MOBILE PAYMENT - THANK YOU",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "Payments & Credits",
                ],
            ]
        )

        result = service.preview_statement(credit_card_account, statement, "amex", "2026-05", "closed")

        assert result.errors == []
        assert result.parsed_count == 2
        assert result.rows[0].posted_date == date(2026, 5, 7)
        assert result.rows[0].description == "APPLE.COM/BILL INTERNET CHARGE CA"
        assert result.rows[0].transaction_type == "debit"
        assert result.rows[0].amount == Decimal("9.99")
        assert result.rows[1].description == "MOBILE PAYMENT - THANK YOU"
        assert result.rows[1].transaction_type == "credit"
        assert result.rows[1].amount == Decimal("500.00")

    def test_preview_amex_activity_fixture_sample(self, credit_card_account):
        service = StatementImportService()
        sample_path = Path(__file__).resolve().parent / "fixtures" / "amex_activity.xlsx"
        statement = io.BytesIO(sample_path.read_bytes())
        statement.name = "activity.xlsx"

        result = service.preview_statement(credit_card_account, statement, "american_express", "2026-05", "closed")

        assert result.errors == []
        assert result.institution == "amex"
        assert result.parsed_count == 1
        assert result.rows[0].posted_date == date(2026, 5, 7)
        assert "APPLE.COM/BILL" in result.rows[0].description
        assert result.rows[0].transaction_type == "debit"
        assert result.rows[0].amount == Decimal("9.99")
