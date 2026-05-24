"""Tests for CSV statement import and reconciliation."""

import io
from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from apps.financial_account.models import FinancialAccount
from apps.financial_account.services.csv_import_service import CSVImportService
from apps.financial_account.services.statement_file_service import StatementFileService
from apps.financial_account.services.statement_import_service import (
    StatementImportResult,
    StatementImportService,
)
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


@pytest.fixture
def user(db):
    return User.objects.create_user(username="csvtest", email="csv@test.com", password="testpass123")


@pytest.fixture
def account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="CSV Test Checking",
        account_type="checking",
        balance=Decimal("1000.00"),
    )


@pytest.fixture
def credit_card_account(user):
    return FinancialAccount.objects.create(
        user=user,
        name="CSV Test CC",
        account_type="credit_card",
        balance=Decimal("-500.00"),
        is_liability=True,
    )


@pytest.fixture
def service():
    return CSVImportService()


def _make_csv(rows_text: str) -> io.StringIO:
    return io.StringIO(rows_text)


def _make_named_csv(rows_text: str, name: str = "statement.csv") -> io.BytesIO:
    csv_file = io.BytesIO(rows_text.encode())
    csv_file.name = name
    return csv_file


def _make_xlsx(rows: list[dict], name: str = "statement.xlsx") -> io.BytesIO:
    xlsx_file = io.BytesIO()
    pd.DataFrame(rows).to_excel(xlsx_file, index=False)
    xlsx_file.seek(0)
    xlsx_file.name = name
    return xlsx_file


def _make_bofa_checking_statement() -> io.BytesIO:
    return _make_named_csv(
        "Description,,Summary Amt.\n"
        'Beginning balance as of 05/13/2026,,"723.98"\n'
        'Total credits,,"547.74"\n'
        'Total debits,,"-821.00"\n'
        'Ending balance as of 05/23/2026,,"450.72"\n'
        "\n"
        "Date,Description,Amount,Running Bal.\n"
        '05/13/2026,Beginning balance as of 05/13/2026,,"723.98"\n'
        '05/13/2026,"Monthly Maintenance Fee","-12.00","711.98"\n'
        '05/15/2026,"VENMO DES:CASHOUT","447.74","1,159.72"\n'
        '05/15/2026,"GUSTO PAYROLL DES:PAYROLL","100.00","1,259.72"\n'
        '05/18/2026,"VENMO DES:PAYMENT","-809.00","450.72"\n'
    )


class TestCSVImportBasic:
    """Basic CSV import functionality."""

    def test_import_valid_csv(self, service, account):
        csv_data = _make_csv(
            "date,amount,description,type\n2025-06-01,50.00,Coffee Shop,debit\n2025-06-02,1500.00,Paycheck,credit\n"
        )
        result = service.import_statement(account, csv_data)

        assert result.imported_count == 2
        assert result.skipped_duplicates == 0
        assert len(result.errors) == 0
        assert Transaction.objects.filter(account=account, sync_source="csv").count() == 2

        account.refresh_from_db()
        # 1000 - 50 + 1500 = 2450
        assert account.balance == Decimal("2450.00")

    def test_import_empty_csv(self, service, account):
        csv_data = _make_csv("date,amount,description\n")
        result = service.import_statement(account, csv_data)

        assert result.imported_count == 0
        assert "No valid transactions found" in result.errors[0]

    def test_import_infers_type_from_sign(self, service, account):
        csv_data = _make_csv("date,amount,description\n2025-06-01,-75.00,Grocery Store\n2025-06-02,200.00,Refund\n")
        result = service.import_statement(account, csv_data)

        assert result.imported_count == 2
        txns = Transaction.objects.filter(account=account, sync_source="csv").order_by("date")
        assert txns[0].transaction_type == "debit"
        assert txns[0].amount == Decimal("75.00")
        assert txns[1].transaction_type == "credit"
        assert txns[1].amount == Decimal("200.00")

    def test_import_mixed_credit_debit(self, service, account):
        csv_data = _make_csv(
            "date,amount,description,type\n"
            "2025-06-01,100.00,Purchase,debit\n"
            "2025-06-01,50.00,Refund,credit\n"
            "2025-06-02,200.00,Rent,debit\n"
        )
        result = service.import_statement(account, csv_data)
        assert result.imported_count == 3

        account.refresh_from_db()
        # 1000 - 100 + 50 - 200 = 750
        assert account.balance == Decimal("750.00")


class TestCSVReconciliation:
    """Reconciliation against statement ending balance."""

    def test_matching_ending_balance(self, service, account):
        csv_data = _make_csv("date,amount,description,type\n2025-06-01,100.00,Purchase,debit\n")
        # Account starts at 1000, after -100 = 900
        result = service.import_statement(account, csv_data, ending_balance=Decimal("900.00"))

        assert result.imported_count == 1
        assert result.discrepancy == Decimal("0")
        assert result.adjustment_amount is None

    def test_mismatched_ending_balance_creates_adjustment(self, service, account):
        csv_data = _make_csv("date,amount,description,type\n2025-06-01,100.00,Purchase,debit\n")
        # Account after import = 900, but statement says 850
        result = service.import_statement(account, csv_data, ending_balance=Decimal("850.00"))

        assert result.imported_count == 1
        assert result.discrepancy == Decimal("-50.00")
        assert result.adjustment_amount == Decimal("-50.00")

        account.refresh_from_db()
        assert account.balance == Decimal("850.00")

        # Should have created a Balance Adjustment transaction
        adj = Transaction.objects.filter(account=account, description__contains="Balance Adjustment").first()
        assert adj is not None
        assert adj.amount == Decimal("50.00")
        assert adj.transaction_type == "debit"
        assert adj.status == "reconciled"

    def test_positive_discrepancy_creates_credit_adjustment(self, service, account):
        csv_data = _make_csv("date,amount,description,type\n2025-06-01,100.00,Purchase,debit\n")
        # Account after import = 900, but statement says 1000
        result = service.import_statement(account, csv_data, ending_balance=Decimal("1000.00"))

        assert result.discrepancy == Decimal("100.00")
        account.refresh_from_db()
        assert account.balance == Decimal("1000.00")

        adj = Transaction.objects.filter(account=account, description__contains="Balance Adjustment").first()
        assert adj.transaction_type == "credit"
        assert adj.amount == Decimal("100.00")


class TestCSVDuplicateDetection:
    """Duplicate detection prevents re-importing the same CSV."""

    def test_duplicate_csv_skipped(self, service, account):
        csv_text = "date,amount,description,type\n2025-06-01,50.00,Coffee,debit\n2025-06-02,100.00,Lunch,debit\n"

        result1 = service.import_statement(account, _make_csv(csv_text))
        assert result1.imported_count == 2
        assert result1.skipped_duplicates == 0

        result2 = service.import_statement(account, _make_csv(csv_text))
        assert result2.imported_count == 0
        assert result2.skipped_duplicates == 2

    def test_partial_overlap(self, service, account):
        csv1 = "date,amount,description,type\n2025-06-01,50.00,Coffee,debit\n"
        csv2 = "date,amount,description,type\n2025-06-01,50.00,Coffee,debit\n2025-06-02,75.00,Dinner,debit\n"

        result1 = service.import_statement(account, _make_csv(csv1))
        assert result1.imported_count == 1

        result2 = service.import_statement(account, _make_csv(csv2))
        assert result2.imported_count == 1
        assert result2.skipped_duplicates == 1


class TestCSVInvalidFormat:
    """Invalid CSV formats produce appropriate errors."""

    def test_missing_required_columns(self, service, account):
        csv_data = _make_csv("foo,bar\n1,2\n")
        result = service.import_statement(account, csv_data)

        assert result.imported_count == 0
        assert any("Missing required columns" in e for e in result.errors)

    def test_invalid_date(self, service, account):
        csv_data = _make_csv("date,amount,description\nnot-a-date,50.00,Coffee\n")
        result = service.import_statement(account, csv_data)
        assert result.imported_count == 0
        assert any("invalid date" in e for e in result.errors)

    def test_invalid_amount(self, service, account):
        csv_data = _make_csv("date,amount,description\n2025-06-01,not-a-number,Coffee\n")
        result = service.import_statement(account, csv_data)
        assert result.imported_count == 0
        assert any("invalid amount" in e for e in result.errors)

    def test_mixed_valid_and_invalid_rows(self, service, account):
        csv_data = _make_csv(
            "date,amount,description,type\n"
            "2025-06-01,50.00,Good row,debit\n"
            "bad-date,25.00,Bad row,debit\n"
            "2025-06-03,75.00,Another good row,debit\n"
        )
        result = service.import_statement(account, csv_data)
        assert result.imported_count == 2
        assert len(result.errors) == 1


class TestCSVCreditCardImport:
    """CSV import into credit card accounts (negative balances)."""

    def test_import_into_credit_card(self, service, credit_card_account):
        csv_data = _make_csv("date,amount,description,type\n2025-06-01,200.00,Restaurant,debit\n")
        result = service.import_statement(credit_card_account, csv_data)
        assert result.imported_count == 1

        credit_card_account.refresh_from_db()
        # -500 + (-200) = -700
        assert credit_card_account.balance == Decimal("-700.00")

    def test_reconcile_credit_card(self, service, credit_card_account):
        csv_data = _make_csv("date,amount,description,type\n2025-06-01,100.00,Payment,credit\n")
        # After import: -500 + 100 = -400, statement says -350
        result = service.import_statement(
            credit_card_account,
            csv_data,
            ending_balance=Decimal("-350.00"),
        )

        assert result.discrepancy == Decimal("50.00")
        credit_card_account.refresh_from_db()
        assert credit_card_account.balance == Decimal("-350.00")


class TestStatementImportService:
    """CSV/Excel statement import preview and commit behavior."""

    def test_preview_bank_of_america_csv(self, account):
        service = StatementImportService()
        statement = _make_named_csv(
            "Posted Date,Payee,Amount\n2025-06-01,Coffee Shop,-5.25\n2025-06-02,Payroll,1500.00\n"
        )

        result = service.preview_statement(account, statement, "bofa", "2025-06")

        assert result.parsed_count == 2
        assert result.duplicate_count == 0
        assert result.rows[0].transaction_type == "debit"
        assert result.rows[1].transaction_type == "credit"
        assert result.rows[0].source_row_hash

    def test_preview_bank_of_america_parses_zelle_memo_quotes(self, account):
        service = StatementImportService()
        statement = _make_named_csv(
            "Description,,Summary Amt.\n"
            'Beginning balance as of 01/12/2026,,"1,830.69"\n'
            'Ending balance as of 01/12/2026,,"1,884.56"\n'
            "\n"
            "Date,Description,Amount,Running Bal.\n"
            '01/12/2026,"Zelle payment from MOHAMED E L KHAIRIL for "ribs, chicken, parking, chipotle"; Conf# hgccZkfYc","60.67","1,891.36"\n'
            '01/12/2026,"Online Banking payment to CRD 8737 Confirmation# 4206190553","-72.81","1,884.56"\n'
        )

        result = service.preview_statement(account, statement, "bofa", "2026-01")

        assert result.errors == []
        assert result.parsed_count == 2
        assert (
            result.rows[0].description
            == 'Zelle payment from MOHAMED E L KHAIRIL for "ribs, chicken, parking, chipotle"; Conf# hgccZkfYc'
        )
        assert result.rows[0].amount == Decimal("60.67")
        assert result.rows[1].description == "Online Banking payment to CRD 8737 Confirmation# 4206190553"

    def test_preview_bank_of_america_zelle_quotes_without_bofa_institution(self, account):
        service = StatementImportService()
        statement = _make_named_csv(
            "Description,,Summary Amt.\n"
            'Beginning balance as of 01/12/2026,,"1,830.69"\n'
            'Ending balance as of 01/12/2026,,"1,884.56"\n'
            "\n"
            "Date,Description,Amount,Running Bal.\n"
            '01/12/2026,"Zelle payment from MOHAMED E L KHAIRIL for "ribs, chicken, parking, chipotle"; Conf# hgccZkfYc","60.67","1,891.36"\n'
        )

        result = service.preview_statement(account, statement, "chase", "2026-01")

        assert result.errors == []
        assert result.parsed_count == 1
        assert "ribs, chicken, parking, chipotle" in result.rows[0].description

    def test_preview_bank_of_america_parses_comma_thousands_in_summary_balances(self, account):
        service = StatementImportService()
        statement = _make_named_csv(
            "Description,,Summary Amt.\n"
            'Beginning balance as of 11/25/2024,,"1,617.51"\n'
            'Total credits,,"93,312.65"\n'
            'Total debits,,"-94,218.18"\n'
            'Ending balance as of 11/25/2024,,"1,555.33"\n'
            "\n"
            "Date,Description,Amount,Running Bal.\n"
            '11/25/2024,Beginning balance as of 11/25/2024,,"1,617.51"\n'
            '11/25/2024,"Online Banking payment to CRD 8737 Confirmation# 4057021018","-62.18","1,555.33"\n'
        )

        result = service.preview_statement(account, statement, "bofa", "2024-11")

        assert result.balance_summary == {
            "beginning_balance": "1617.51",
            "ending_balance": "1555.33",
            "beginning_date": "2024-11-25",
            "ending_date": "2024-11-25",
        }
        assert result.reconciliation["statement_internal_ok"] is True
        assert not any("running balance" in warning.lower() for warning in result.reconciliation_warnings)

    def test_preview_bank_of_america_corrects_misparsed_summary_from_transaction_row(self, account):
        service = StatementImportService()
        statement = _make_named_csv(
            "Description,,Summary Amt.\n"
            'Beginning balance as of 11/25/2024,,"1,617.51"\n'
            'Ending balance as of 11/25/2024,,"1,555.33"\n'
            "\n"
            "Date,Description,Amount,Running Bal.\n"
            '11/25/2024,Beginning balance as of 11/25/2024,,"1,617.51"\n'
            '11/25/2024,"Online Banking payment to CRD 8737 Confirmation# 4057021018","-62.18","1,555.33"\n'
        )
        content = statement.read()
        frame = service._read_frame(content, ".csv", institution="bofa")
        summary = service._parse_bofa_balance_summary(content)
        summary["beginning_balance"] = "617.51"
        corrected = service._correct_bofa_summary_from_transactions(summary, frame)

        assert corrected["beginning_balance"] == "1617.51"

        statement.seek(0)
        result = service.preview_statement(account, statement, "bofa", "2024-11")
        assert result.balance_summary["beginning_balance"] == "1617.51"
        assert result.reconciliation["statement_internal_ok"] is True

    def test_preview_bank_of_america_download_csv_with_summary_preamble(self, account):
        service = StatementImportService()
        statement = _make_bofa_checking_statement()

        result = service.preview_statement(account, statement, "bofa", "2026-05")

        assert result.errors == []
        assert result.parsed_count == 4
        assert result.rows[0].description == "Monthly Maintenance Fee"
        assert result.rows[0].amount == Decimal("12.00")
        assert result.rows[0].transaction_type == "debit"
        assert result.rows[1].amount == Decimal("447.74")
        assert result.rows[1].transaction_type == "credit"
        assert result.rows[2].amount == Decimal("100.00")
        assert result.rows[2].transaction_type == "credit"
        assert result.rows[3].amount == Decimal("809.00")
        assert result.rows[3].transaction_type == "debit"
        assert result.balance_summary == {
            "beginning_balance": "723.98",
            "ending_balance": "450.72",
            "beginning_date": "2026-05-13",
            "ending_date": "2026-05-23",
        }
        assert result.reconciliation["statement_internal_ok"] is True
        assert result.reconciliation["opening_balance_action"] == "available_create"
        assert result.reconciliation_warnings == []

    def test_import_bank_of_america_checking_without_flag_leaves_opening_balance_unchanged(self, user):
        service = StatementImportService()
        account = FinancialAccount.objects.create(
            user=user,
            name="BoFA Checking",
            account_type="checking",
            balance=Decimal("0"),
        )
        statement = _make_bofa_checking_statement()

        result = service.import_statement(account, statement, "bofa", "2026-05", "closed")

        account.refresh_from_db()

        assert result.imported_count == 4
        assert result.reconciliation["opening_balance_action"] == "available_create"
        assert result.reconciliation["opening_balance_applied"] is False
        assert not Transaction.objects.filter(account=account, description="Opening Balance").exists()
        assert result.reconciliation["account_ending_ok"] is False
        assert any("opening balance was not changed" in warning.lower() for warning in result.reconciliation_warnings)

    def test_import_bank_of_america_checking_with_flag_creates_opening_balance_and_reconciles(self, user):
        service = StatementImportService()
        account = FinancialAccount.objects.create(
            user=user,
            name="BoFA Checking",
            account_type="checking",
            balance=Decimal("0"),
        )
        statement = _make_bofa_checking_statement()

        result = service.import_statement(
            account,
            statement,
            "bofa",
            "2026-05",
            "closed",
            apply_opening_balance=True,
        )

        account.refresh_from_db()
        opening = Transaction.objects.get(account=account, description="Opening Balance")

        assert result.imported_count == 4
        assert result.reconciliation["opening_balance_action"] == "create"
        assert result.reconciliation["opening_balance_applied"] is True
        assert result.reconciliation["account_ending_ok"] is True
        assert result.reconciliation["account_ending_discrepancy"] == "0.00"
        assert result.reconciliation_warnings == []
        assert opening.amount == Decimal("723.98")
        assert opening.transaction_type == "credit"
        assert opening.date.isoformat() == "2026-05-13"
        assert account.balance == Decimal("450.72")

    def test_preview_bank_of_america_flags_internal_total_mismatch(self, account):
        service = StatementImportService()
        statement = _make_named_csv(
            "Description,,Summary Amt.\n"
            'Beginning balance as of 05/13/2026,,"723.98"\n'
            'Ending balance as of 05/23/2026,,"999.99"\n'
            "\n"
            "Date,Description,Amount,Running Bal.\n"
            '05/13/2026,"Monthly Maintenance Fee","-12.00","711.98"\n'
        )

        result = service.preview_statement(account, statement, "bofa", "2026-05")

        assert result.reconciliation["statement_internal_ok"] is False
        assert len(result.reconciliation_warnings) >= 1
        assert "Statement totals are inconsistent" in result.reconciliation_warnings[0]

    def test_preview_bank_of_america_flags_running_balance_mismatch(self, account):
        service = StatementImportService()
        statement = _make_named_csv(
            "Description,,Summary Amt.\n"
            'Beginning balance as of 05/13/2026,,"723.98"\n'
            'Ending balance as of 05/23/2026,,"711.98"\n'
            "\n"
            "Date,Description,Amount,Running Bal.\n"
            '05/13/2026,"Monthly Maintenance Fee","-12.00","700.00"\n'
        )

        result = service.preview_statement(account, statement, "bofa", "2026-05")

        assert result.reconciliation["statement_internal_ok"] is True
        assert "running balance" in result.reconciliation_warnings[0].lower()

    def test_import_bank_of_america_without_flag_keeps_existing_opening_balance(self, user):
        service = StatementImportService()
        account = FinancialAccount.objects.create(
            user=user,
            name="BoFA Checking",
            account_type="checking",
            balance=Decimal("0"),
        )
        Transaction.objects.create(
            user=user,
            account=account,
            date=date(2026, 5, 1),
            amount=Decimal("500.00"),
            transaction_type="credit",
            description="Opening Balance",
            sync_source="manual",
            status="reconciled",
        )
        account.refresh_from_db()
        statement = _make_bofa_checking_statement()

        result = service.import_statement(account, statement, "bofa", "2026-05", "closed")

        opening = Transaction.objects.get(account=account, description="Opening Balance")
        account.refresh_from_db()

        assert result.reconciliation["opening_balance_action"] == "available_update"
        assert result.reconciliation["opening_balance_applied"] is False
        assert result.reconciliation["account_opening_balance_current"] == "500.00"
        assert opening.amount == Decimal("500.00")
        assert opening.date.isoformat() == "2026-05-01"
        assert result.reconciliation["account_ending_ok"] is False

    def test_import_bank_of_america_with_flag_updates_existing_opening_balance(self, user):
        service = StatementImportService()
        account = FinancialAccount.objects.create(
            user=user,
            name="BoFA Checking",
            account_type="checking",
            balance=Decimal("0"),
        )
        Transaction.objects.create(
            user=user,
            account=account,
            date=date(2026, 5, 1),
            amount=Decimal("500.00"),
            transaction_type="credit",
            description="Opening Balance",
            sync_source="manual",
            status="reconciled",
        )
        account.refresh_from_db()
        statement = _make_bofa_checking_statement()

        result = service.import_statement(
            account,
            statement,
            "bofa",
            "2026-05",
            "closed",
            apply_opening_balance=True,
        )

        opening = Transaction.objects.get(account=account, description="Opening Balance")
        account.refresh_from_db()

        assert result.reconciliation["opening_balance_action"] == "update"
        assert result.reconciliation["opening_balance_applied"] is True
        assert opening.amount == Decimal("723.98")
        assert opening.date.isoformat() == "2026-05-13"
        assert account.balance == Decimal("450.72")
        assert result.reconciliation["account_ending_ok"] is True

    def test_import_skips_overlapping_statement_rows(self, account):
        service = StatementImportService()
        first_statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n",
            "first.csv",
        )
        overlapping_statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n2025-06-02,Dinner,-20.00\n",
            "second.csv",
        )

        first_result = service.import_statement(account, first_statement, "chase", "2025-06", "provisional")
        second_result = service.import_statement(account, overlapping_statement, "chase", "2025-06", "closed")

        assert first_result.imported_count == 1
        assert second_result.imported_count == 1
        assert second_result.duplicate_count == 1
        assert Transaction.objects.filter(account=account, sync_source="csv").count() == 2

    def test_preview_flags_possible_changed_pending_row(self, account):
        service = StatementImportService()
        provisional_statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n",
            "provisional.csv",
        )
        closed_statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.75\n",
            "closed.csv",
        )

        service.import_statement(account, provisional_statement, "chase", "2025-06", "provisional")
        result = service.preview_statement(account, closed_statement, "chase", "2025-06", "closed")

        assert result.possible_changed_count == 1
        assert result.rows[0].status == "possible_changed"

    def test_preview_american_express_xlsx(self, credit_card_account):
        service = StatementImportService()
        statement = _make_xlsx(
            [
                {
                    "Date": "2025-06-01",
                    "Description": "Restaurant",
                    "Amount": "42.12",
                }
            ]
        )

        result = service.preview_statement(credit_card_account, statement, "amex", "2025-06", "closed")

        assert result.parsed_count == 1
        assert result.rows[0].transaction_type == "debit"
        assert result.rows[0].amount == Decimal("42.12")

    @pytest.mark.parametrize(
        "institution",
        [
            "bofa",
            "marcus",
            "amex",
            "robinhood_bank",
            "fidelity",
            "robinhood_investments",
            "guideline",
            "chase",
        ],
    )
    def test_all_target_institutions_have_csv_adapter(self, account, institution):
        service = StatementImportService()
        statement = _make_named_csv("Date,Description,Amount\n2025-06-01,Sample,-1.23\n")

        result = service.preview_statement(account, statement, institution, "2025-06")

        assert result.parsed_count == 1
        assert result.rows[0].institution == institution

    def test_closed_statement_finalizes_matching_provisional_rows(self, account):
        service = StatementImportService()
        provisional_statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n",
            "provisional.csv",
        )
        closed_statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n",
            "closed.csv",
        )

        service.import_statement(account, provisional_statement, "chase", "2025-06", "provisional")
        transaction = Transaction.objects.get(account=account, description="Coffee")
        assert transaction.status == "pending"

        service.import_statement(account, closed_statement, "chase", "2025-06", "closed")
        transaction.refresh_from_db()
        assert transaction.status == "posted"


class TestStatementFileService:
    """Google Drive statement file library behavior."""

    def _drive_account(self, account, folder_id="test-folder"):
        account.storage_uri = f"gdrive://{folder_id}"
        account.save(update_fields=["storage_uri"])
        return account

    def test_upload_stores_statement_in_drive(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n",
            "june.csv",
        )

        result = service.save_upload(
            user=account.user,
            account=account,
            uploaded_file=statement,
            institution="chase",
            statement_period="2025-06",
            statement_status="provisional",
        )

        assert result.created is True
        assert result.statement.statement_year == 2025
        assert result.statement.statement_month == 6
        assert result.statement.stored_path.startswith("gdrive://test-folder/")
        assert fake_drive_storage.files_by_folder["test-folder"]

    def test_upload_stores_custom_cross_year_period(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2026-01-10,Coffee,-5.00\n",
            "cross-year.csv",
        )

        result = service.save_upload(
            user=account.user,
            account=account,
            uploaded_file=statement,
            institution="chase",
            statement_period="2025-10-15 to 2026-01-14",
            statement_status="closed",
            statement_year=2026,
            statement_month=1,
        )

        assert result.created is True
        assert result.statement.statement_period == "2025-10-15 to 2026-01-14"
        assert result.statement.statement_year == 2026
        assert result.statement.statement_month == 1

        imported = service.import_statement(result.statement)
        assert imported.imported_count == 1
        assert Transaction.objects.filter(account=account, sync_source="csv").count() == 1

    def test_upload_rejects_statement_period_over_max_length(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        statement = _make_named_csv(
            "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n",
            "june.csv",
        )

        with pytest.raises(ValueError, match="statement_period must be 40 characters or fewer"):
            service.save_upload(
                user=account.user,
                account=account,
                uploaded_file=statement,
                institution="chase",
                statement_period="x" * 41,
            )

    def test_duplicate_upload_returns_existing_record(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        csv_text = "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"

        first = service.save_upload(account.user, account, _make_named_csv(csv_text), "chase", "2025-06")
        second = service.save_upload(account.user, account, _make_named_csv(csv_text), "chase", "2025-06")

        assert first.created is True
        assert second.created is False
        assert second.statement.id == first.statement.id

    def test_preview_and_import_update_statement_summary(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        upload = service.save_upload(
            account.user,
            account,
            _make_named_csv("Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"),
            "chase",
            "2025-06",
            "closed",
        )

        preview = service.preview_statement(upload.statement)
        upload.statement.refresh_from_db()
        assert preview.parsed_count == 1
        assert upload.statement.import_status == "previewed"
        assert upload.statement.parsed_count == 1

        imported = service.import_statement(upload.statement)
        upload.statement.refresh_from_db()
        assert imported.imported_count == 1
        assert upload.statement.import_status == "imported"
        assert upload.statement.imported_count == 1
        assert Transaction.objects.filter(account=account, sync_source="csv").count() == 1

    def test_update_statement_keeps_drive_file_when_period_changes(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        upload = service.save_upload(
            account.user,
            account,
            _make_named_csv("Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"),
            "chase",
            "2025-06",
        )
        stored_path = upload.statement.stored_path

        updated = service.update_statement(upload.statement, statement_period="2025-07")

        assert updated.statement_month == 7
        assert updated.stored_path == stored_path
        assert fake_drive_storage.files_by_folder["test-folder"]

    def test_acknowledge_reconciliation_clears_warning_state(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        upload = service.save_upload(
            account.user,
            account,
            _make_named_csv("Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"),
            "chase",
            "2025-06",
        )
        upload.statement.last_import_result = {"reconciliation_warnings": ["Example warning"]}
        upload.statement.save(update_fields=["last_import_result", "updated_at"])

        acknowledged = service.acknowledge_reconciliation(upload.statement)
        assert acknowledged.reconciliation_acknowledged_at is not None

        result = StatementImportResult()
        result.reconciliation_warnings = ["Example warning"]
        service._update_import_summary(acknowledged, result, "previewed")
        acknowledged.refresh_from_db()
        assert acknowledged.reconciliation_acknowledged_at is None

    def test_acknowledge_reconciliation_requires_warnings(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        upload = service.save_upload(
            account.user,
            account,
            _make_named_csv("Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"),
            "chase",
            "2025-06",
        )

        with pytest.raises(ValueError, match="No reconciliation warnings to acknowledge"):
            service.acknowledge_reconciliation(upload.statement)

    def test_list_statements_reconciles_missing_drive_files(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        upload = service.save_upload(
            account.user,
            account,
            _make_named_csv("Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"),
            "chase",
            "2025-06",
        )
        folder_id = "test-folder"
        stored_name = next(iter(fake_drive_storage.files_by_folder[folder_id]))
        del fake_drive_storage.files_by_folder[folder_id][stored_name]

        rows = list(service.list_statements(account.user, account_id=account.id))

        assert rows == []
        upload.statement.refresh_from_db()
        assert upload.statement.is_deleted is True

    def test_soft_delete_removes_stored_drive_file(self, account, fake_drive_storage, monkeypatch):
        monkeypatch.setattr(
            "apps.financial_account.storage.factory.GoogleDriveStatementStorage",
            lambda: fake_drive_storage,
        )
        service = StatementFileService()
        self._drive_account(account)
        upload = service.save_upload(
            account.user,
            account,
            _make_named_csv("Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"),
            "chase",
            "2025-06",
        )

        service.soft_delete_statement(upload.statement)

        assert fake_drive_storage.files_by_folder["test-folder"] == {}
        upload.statement.refresh_from_db()
        assert upload.statement.is_deleted is True
