"""Tests for CSV statement import and reconciliation."""

import io
from decimal import Decimal

import pandas as pd
import pytest

from apps.financial_account.models import FinancialAccount
from apps.financial_account.services.csv_import_service import CSVImportService
from apps.financial_account.services.statement_file_service import StatementFileService
from apps.financial_account.services.statement_import_service import (
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
    """Local statement file library behavior."""

    def test_upload_stores_statement_by_account_year_month(self, account, tmp_path):
        service = StatementFileService()
        service.storage_root = tmp_path / "statements"
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
        assert str(account.id) in result.statement.stored_path
        assert service._absolute_path(result.statement.stored_path).exists()

    def test_duplicate_upload_returns_existing_record(self, account, tmp_path):
        service = StatementFileService()
        service.storage_root = tmp_path / "statements"
        csv_text = "Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"

        first = service.save_upload(account.user, account, _make_named_csv(csv_text), "chase", "2025-06")
        second = service.save_upload(account.user, account, _make_named_csv(csv_text), "chase", "2025-06")

        assert first.created is True
        assert second.created is False
        assert second.statement.id == first.statement.id

    def test_preview_and_import_update_statement_summary(self, account, tmp_path):
        service = StatementFileService()
        service.storage_root = tmp_path / "statements"
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

    def test_update_statement_moves_file_to_new_period(self, account, tmp_path):
        service = StatementFileService()
        service.storage_root = tmp_path / "statements"
        upload = service.save_upload(
            account.user,
            account,
            _make_named_csv("Transaction Date,Description,Amount\n2025-06-01,Coffee,-5.00\n"),
            "chase",
            "2025-06",
        )
        old_path = service._absolute_path(upload.statement.stored_path)

        updated = service.update_statement(upload.statement, statement_period="2025-07")
        new_path = service._absolute_path(updated.stored_path)

        assert updated.statement_month == 7
        assert not old_path.exists()
        assert new_path.exists()
