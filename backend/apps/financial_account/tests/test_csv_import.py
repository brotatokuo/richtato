"""Tests for CSV statement import and reconciliation."""

import io
from datetime import date
from decimal import Decimal

import pytest
from apps.financial_account.models import FinancialAccount
from apps.financial_account.services.csv_import_service import CSVImportService
from apps.richtato_user.models import User
from apps.transaction.models import Transaction


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="csvtest", email="csv@test.com", password="testpass123"
    )


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


class TestCSVImportBasic:
    """Basic CSV import functionality."""

    def test_import_valid_csv(self, service, account):
        csv_data = _make_csv(
            "date,amount,description,type\n"
            "2025-06-01,50.00,Coffee Shop,debit\n"
            "2025-06-02,1500.00,Paycheck,credit\n"
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
        csv_data = _make_csv(
            "date,amount,description\n"
            "2025-06-01,-75.00,Grocery Store\n"
            "2025-06-02,200.00,Refund\n"
        )
        result = service.import_statement(account, csv_data)

        assert result.imported_count == 2
        txns = Transaction.objects.filter(account=account, sync_source="csv").order_by(
            "date"
        )
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
        csv_data = _make_csv(
            "date,amount,description,type\n"
            "2025-06-01,100.00,Purchase,debit\n"
        )
        # Account starts at 1000, after -100 = 900
        result = service.import_statement(
            account, csv_data, ending_balance=Decimal("900.00")
        )

        assert result.imported_count == 1
        assert result.discrepancy == Decimal("0")
        assert result.adjustment_amount is None

    def test_mismatched_ending_balance_creates_adjustment(self, service, account):
        csv_data = _make_csv(
            "date,amount,description,type\n"
            "2025-06-01,100.00,Purchase,debit\n"
        )
        # Account after import = 900, but statement says 850
        result = service.import_statement(
            account, csv_data, ending_balance=Decimal("850.00")
        )

        assert result.imported_count == 1
        assert result.discrepancy == Decimal("-50.00")
        assert result.adjustment_amount == Decimal("-50.00")

        account.refresh_from_db()
        assert account.balance == Decimal("850.00")

        # Should have created a Balance Adjustment transaction
        adj = Transaction.objects.filter(
            account=account, description__contains="Balance Adjustment"
        ).first()
        assert adj is not None
        assert adj.amount == Decimal("50.00")
        assert adj.transaction_type == "debit"
        assert adj.status == "reconciled"

    def test_positive_discrepancy_creates_credit_adjustment(self, service, account):
        csv_data = _make_csv(
            "date,amount,description,type\n"
            "2025-06-01,100.00,Purchase,debit\n"
        )
        # Account after import = 900, but statement says 1000
        result = service.import_statement(
            account, csv_data, ending_balance=Decimal("1000.00")
        )

        assert result.discrepancy == Decimal("100.00")
        account.refresh_from_db()
        assert account.balance == Decimal("1000.00")

        adj = Transaction.objects.filter(
            account=account, description__contains="Balance Adjustment"
        ).first()
        assert adj.transaction_type == "credit"
        assert adj.amount == Decimal("100.00")


class TestCSVDuplicateDetection:
    """Duplicate detection prevents re-importing the same CSV."""

    def test_duplicate_csv_skipped(self, service, account):
        csv_text = (
            "date,amount,description,type\n"
            "2025-06-01,50.00,Coffee,debit\n"
            "2025-06-02,100.00,Lunch,debit\n"
        )

        result1 = service.import_statement(account, _make_csv(csv_text))
        assert result1.imported_count == 2
        assert result1.skipped_duplicates == 0

        result2 = service.import_statement(account, _make_csv(csv_text))
        assert result2.imported_count == 0
        assert result2.skipped_duplicates == 2

    def test_partial_overlap(self, service, account):
        csv1 = (
            "date,amount,description,type\n"
            "2025-06-01,50.00,Coffee,debit\n"
        )
        csv2 = (
            "date,amount,description,type\n"
            "2025-06-01,50.00,Coffee,debit\n"
            "2025-06-02,75.00,Dinner,debit\n"
        )

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
        csv_data = _make_csv(
            "date,amount,description\n"
            "not-a-date,50.00,Coffee\n"
        )
        result = service.import_statement(account, csv_data)
        assert result.imported_count == 0
        assert any("invalid date" in e for e in result.errors)

    def test_invalid_amount(self, service, account):
        csv_data = _make_csv(
            "date,amount,description\n"
            "2025-06-01,not-a-number,Coffee\n"
        )
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
        csv_data = _make_csv(
            "date,amount,description,type\n"
            "2025-06-01,200.00,Restaurant,debit\n"
        )
        result = service.import_statement(credit_card_account, csv_data)
        assert result.imported_count == 1

        credit_card_account.refresh_from_db()
        # -500 + (-200) = -700
        assert credit_card_account.balance == Decimal("-700.00")

    def test_reconcile_credit_card(self, service, credit_card_account):
        csv_data = _make_csv(
            "date,amount,description,type\n"
            "2025-06-01,100.00,Payment,credit\n"
        )
        # After import: -500 + 100 = -400, statement says -350
        result = service.import_statement(
            credit_card_account,
            csv_data,
            ending_balance=Decimal("-350.00"),
        )

        assert result.discrepancy == Decimal("50.00")
        credit_card_account.refresh_from_db()
        assert credit_card_account.balance == Decimal("-350.00")
