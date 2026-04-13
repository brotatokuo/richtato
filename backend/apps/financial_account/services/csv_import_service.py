"""Service for CSV statement import with reconciliation."""

import csv
import hashlib
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from loguru import logger

from apps.financial_account.models import FinancialAccount
from apps.financial_account.repositories.account_repository import (
    FinancialAccountRepository,
)
from apps.transaction.models import Transaction


class CSVImportResult:
    """Result of a CSV import operation."""

    def __init__(self):
        self.imported_count = 0
        self.skipped_duplicates = 0
        self.errors: list[str] = []
        self.adjustment_amount: Decimal | None = None
        self.balance_after_import: Decimal | None = None
        self.discrepancy: Decimal | None = None


class CSVImportService:
    """Import transactions from CSV statements and reconcile balances."""

    REQUIRED_COLUMNS = {"date", "amount", "description"}

    def __init__(self):
        self.account_repository = FinancialAccountRepository()

    def import_statement(
        self,
        account: FinancialAccount,
        csv_file,
        ending_balance: Decimal | None = None,
        ending_date: date | None = None,
    ) -> CSVImportResult:
        """Import transactions from a CSV file and optionally reconcile.

        Expected CSV format: date, amount, description, [type]
        - date: YYYY-MM-DD
        - amount: positive decimal
        - description: text
        - type: 'debit' or 'credit' (optional, inferred from sign if absent)

        Args:
            account: Target financial account
            csv_file: File-like object containing CSV data
            ending_balance: Optional statement ending balance for reconciliation
            ending_date: Date of the ending balance

        Returns:
            CSVImportResult with counts and any discrepancy info
        """
        result = CSVImportResult()

        try:
            rows = self._parse_csv(csv_file, result)
        except Exception as e:
            result.errors.append(f"Failed to parse CSV: {str(e)}")
            return result

        if not rows:
            if not result.errors:
                result.errors.append("No valid transactions found in CSV")
            return result

        existing_hashes = self._get_existing_hashes(account)

        transactions_to_create = []
        for row in rows:
            row_hash = self._compute_row_hash(account.id, row)
            if row_hash in existing_hashes:
                result.skipped_duplicates += 1
                continue

            txn_type = row.get("type")
            amount = row["amount"]

            if txn_type is None:
                txn_type = "debit" if amount < 0 else "credit"
                amount = abs(amount)

            transactions_to_create.append(
                Transaction(
                    user=account.user,
                    account=account,
                    date=row["date"],
                    amount=abs(amount),
                    transaction_type=txn_type,
                    description=row["description"],
                    sync_source="csv",
                    status="posted",
                )
            )

        if transactions_to_create:
            for txn in transactions_to_create:
                txn.save()
            result.imported_count = len(transactions_to_create)

        account.refresh_from_db()
        result.balance_after_import = account.balance

        if ending_balance is not None:
            result.discrepancy = ending_balance - account.balance
            if result.discrepancy != Decimal("0"):
                self._create_reconciliation_adjustment(account, ending_balance, ending_date or date.today())
                account.refresh_from_db()
                result.adjustment_amount = result.discrepancy
                result.balance_after_import = account.balance

        return result

    def _parse_csv(self, csv_file, result: CSVImportResult) -> list[dict]:
        """Parse CSV file into a list of transaction dicts."""
        if hasattr(csv_file, "read"):
            content = csv_file.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
        else:
            content = csv_file

        reader = csv.DictReader(io.StringIO(content))

        if not reader.fieldnames:
            result.errors.append("CSV file is empty or has no headers")
            return []

        lower_fields = {f.strip().lower() for f in reader.fieldnames}
        missing = self.REQUIRED_COLUMNS - lower_fields
        if missing:
            result.errors.append(f"Missing required columns: {', '.join(missing)}")
            return []

        field_map = {f.strip().lower(): f for f in reader.fieldnames}

        rows = []
        for line_num, raw_row in enumerate(reader, start=2):
            try:
                txn_date = date.fromisoformat(raw_row[field_map["date"]].strip())
            except (ValueError, KeyError):
                result.errors.append(f"Row {line_num}: invalid date")
                continue

            try:
                amount = Decimal(raw_row[field_map["amount"]].strip().replace(",", ""))
            except (InvalidOperation, KeyError):
                result.errors.append(f"Row {line_num}: invalid amount")
                continue

            description = raw_row.get(field_map["description"], "").strip()
            if not description:
                description = "CSV Import"

            row = {"date": txn_date, "amount": amount, "description": description}

            type_key = field_map.get("type")
            if type_key and raw_row.get(type_key, "").strip().lower() in (
                "debit",
                "credit",
            ):
                row["type"] = raw_row[type_key].strip().lower()

            rows.append(row)

        return rows

    def _get_existing_hashes(self, account: FinancialAccount) -> set:
        """Build a set of hashes from existing transactions for dedup."""
        existing = Transaction.objects.filter(account=account, sync_source="csv").values_list(
            "date", "amount", "description"
        )

        hashes = set()
        for txn_date, amount, description in existing:
            key = f"{account.id}:{txn_date}:{amount}:{description}"
            hashes.add(hashlib.md5(key.encode()).hexdigest())
        return hashes

    def _compute_row_hash(self, account_id: int, row: dict) -> str:
        """Compute a dedup hash for a parsed CSV row."""
        key = f"{account_id}:{row['date']}:{abs(row['amount'])}:{row['description']}"
        return hashlib.md5(key.encode()).hexdigest()

    def _create_reconciliation_adjustment(
        self, account: FinancialAccount, target_balance: Decimal, balance_date: date
    ) -> None:
        """Create a Balance Adjustment transaction to reconcile."""
        account.refresh_from_db(fields=["balance"])
        difference = target_balance - account.balance

        if difference == Decimal("0"):
            return

        txn_type = "credit" if difference > 0 else "debit"
        Transaction.objects.create(
            user=account.user,
            account=account,
            date=balance_date,
            amount=abs(difference),
            transaction_type=txn_type,
            description="Balance Adjustment (CSV Reconciliation)",
            sync_source="csv",
            status="reconciled",
        )

        logger.info(f"Created CSV reconciliation adjustment for account {account.id}: {difference} on {balance_date}")
