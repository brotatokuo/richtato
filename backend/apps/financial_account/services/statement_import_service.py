"""CSV/Excel-first statement import service with institution adapters."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from apps.financial_account.models import FinancialAccount
from apps.transaction.models import Transaction

SUPPORTED_INSTITUTIONS = {
    "bofa": {
        "display_name": "Bank of America",
        "domains": ["banking", "credit_card"],
        "date": ["Posted Date", "Transaction Date", "Date"],
        "description": ["Payee", "Description", "Description Original"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
    "marcus": {
        "display_name": "Marcus",
        "domains": ["banking"],
        "date": ["Date", "Transaction Date", "Post Date"],
        "description": ["Description", "Details", "Transaction"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
    "amex": {
        "display_name": "American Express",
        "domains": ["credit_card"],
        "date": ["Date", "Transaction Date"],
        "description": ["Description", "Appears On Your Statement As"],
        "amount": ["Amount"],
        "debit": ["Debit", "Charge"],
        "credit": ["Credit", "Payment"],
    },
    "robinhood_bank": {
        "display_name": "Robinhood Bank",
        "domains": ["banking"],
        "date": ["Date", "Transaction Date", "Posted Date"],
        "description": ["Description", "Memo", "Details"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
    "fidelity": {
        "display_name": "Fidelity",
        "domains": ["investment"],
        "date": ["Run Date", "Date", "Settlement Date", "Trade Date"],
        "description": ["Description", "Action", "Name"],
        "amount": ["Amount", "Cash Amount", "Net Amount"],
        "debit": ["Debit"],
        "credit": ["Credit"],
        "activity": ["Action", "Activity Type", "Type"],
        "symbol": ["Symbol"],
        "quantity": ["Quantity", "Shares"],
    },
    "robinhood_investments": {
        "display_name": "Robinhood Investments",
        "domains": ["investment"],
        "date": ["Activity Date", "Date", "Trade Date"],
        "description": ["Description", "Instrument", "Trans Code"],
        "amount": ["Amount", "Value", "Net Amount"],
        "debit": ["Debit"],
        "credit": ["Credit"],
        "activity": ["Activity Type", "Trans Code", "Type"],
        "symbol": ["Symbol"],
        "quantity": ["Quantity"],
    },
    "guideline": {
        "display_name": "Guideline",
        "domains": ["retirement"],
        "date": ["Date", "Transaction Date", "Payroll Date"],
        "description": ["Description", "Transaction Type", "Fund"],
        "amount": ["Amount", "Value"],
        "debit": ["Debit"],
        "credit": ["Credit", "Contribution"],
        "activity": ["Transaction Type", "Type", "Activity"],
        "symbol": ["Fund", "Symbol"],
        "quantity": ["Shares", "Units", "Quantity"],
    },
    "chase": {
        "display_name": "Chase",
        "domains": ["banking", "credit_card"],
        "date": ["Transaction Date", "Post Date", "Date"],
        "description": ["Description", "Payee"],
        "amount": ["Amount"],
        "debit": ["Debit", "Withdrawal"],
        "credit": ["Credit", "Deposit"],
    },
}


@dataclass
class NormalizedStatementRow:
    """Canonical transaction row emitted by institution parsers."""

    row_number: int
    posted_date: date
    description: str
    amount: Decimal
    transaction_type: str
    institution: str
    source_file_hash: str
    source_row_hash: str
    source_row_hash_base: str
    account_hint: str = ""
    statement_period: str = ""
    activity_type: str = ""
    symbol: str = ""
    quantity: str = ""
    status: str = "new"
    raw_data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Serialize a normalized row for API responses."""
        return {
            "row_number": self.row_number,
            "posted_date": self.posted_date.isoformat(),
            "description": self.description,
            "amount": str(self.amount),
            "transaction_type": self.transaction_type,
            "institution": self.institution,
            "source_file_hash": self.source_file_hash,
            "source_row_hash": self.source_row_hash,
            "account_hint": self.account_hint,
            "statement_period": self.statement_period,
            "activity_type": self.activity_type,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "status": self.status,
        }


@dataclass
class StatementImportResult:
    """Preview or commit result for a statement import."""

    parsed_count: int = 0
    imported_count: int = 0
    duplicate_count: int = 0
    invalid_count: int = 0
    possible_changed_count: int = 0
    errors: list[str] = field(default_factory=list)
    rows: list[NormalizedStatementRow] = field(default_factory=list)
    file_hash: str = ""
    institution: str = ""
    statement_status: str = "provisional"

    def as_dict(self) -> dict[str, Any]:
        """Serialize the import result for API responses."""
        return {
            "parsed_count": self.parsed_count,
            "imported_count": self.imported_count,
            "duplicate_count": self.duplicate_count,
            "invalid_count": self.invalid_count,
            "possible_changed_count": self.possible_changed_count,
            "errors": self.errors,
            "file_hash": self.file_hash,
            "institution": self.institution,
            "statement_status": self.statement_status,
            "rows": [row.as_dict() for row in self.rows],
        }


class StatementImportService:
    """Import transactions from CSV, XLS, and XLSX institution statements."""

    SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}

    def get_supported_institutions(self) -> list[dict[str, Any]]:
        """Return institution metadata for frontend selectors."""
        return [
            {
                "id": institution_id,
                "display_name": config["display_name"],
                "domains": config["domains"],
                "file_types": ["csv", "xls", "xlsx"],
            }
            for institution_id, config in SUPPORTED_INSTITUTIONS.items()
        ]

    def preview_statement(
        self,
        account: FinancialAccount,
        statement_file,
        institution: str,
        statement_period: str = "",
        statement_status: str = "provisional",
    ) -> StatementImportResult:
        """Parse and classify a statement without creating transactions."""
        result = self._parse_statement(account, statement_file, institution, statement_period, statement_status)
        self._classify_rows(account, result)
        return result

    def import_statement(
        self,
        account: FinancialAccount,
        statement_file,
        institution: str,
        statement_period: str = "",
        statement_status: str = "provisional",
    ) -> StatementImportResult:
        """Parse, deduplicate, and create transactions for new statement rows."""
        result = self.preview_statement(account, statement_file, institution, statement_period, statement_status)
        transactions = []

        if statement_status == "closed":
            self._finalize_duplicate_rows(account, result.rows)

        for row in result.rows:
            if row.status != "new":
                continue

            transactions.append(
                Transaction(
                    user=account.user,
                    account=account,
                    date=row.posted_date,
                    amount=row.amount,
                    transaction_type=row.transaction_type,
                    description=row.description,
                    sync_source="csv",
                    external_id=row.source_row_hash,
                    status="posted" if statement_status == "closed" else "pending",
                    raw_data={
                        "institution": row.institution,
                        "statement_period": row.statement_period,
                        "statement_status": statement_status,
                        "source_file_hash": row.source_file_hash,
                        "source_row_hash": row.source_row_hash,
                        "source_row_hash_base": row.source_row_hash_base,
                        "activity_type": row.activity_type,
                        "symbol": row.symbol,
                        "quantity": row.quantity,
                        "raw_row": row.raw_data,
                    },
                )
            )

        for transaction in transactions:
            transaction.save()

        result.imported_count = len(transactions)
        logger.info(
            "Imported statement rows",
            account_id=account.id,
            institution=institution,
            imported=result.imported_count,
            duplicates=result.duplicate_count,
        )
        return result

    def _finalize_duplicate_rows(self, account: FinancialAccount, rows: list[NormalizedStatementRow]) -> None:
        """Mark matching provisional rows as posted when a closed statement confirms them."""
        duplicate_hashes = [row.source_row_hash for row in rows if row.status == "duplicate"]
        if not duplicate_hashes:
            return

        Transaction.objects.filter(
            account=account,
            sync_source="csv",
            external_id__in=duplicate_hashes,
            status="pending",
        ).update(status="posted")

    def _parse_statement(
        self,
        account: FinancialAccount,
        statement_file,
        institution: str,
        statement_period: str,
        statement_status: str,
    ) -> StatementImportResult:
        result = StatementImportResult(institution=institution, statement_status=statement_status)
        config = SUPPORTED_INSTITUTIONS.get(institution)
        if config is None:
            result.errors.append(f"Unsupported institution: {institution}")
            return result

        filename = getattr(statement_file, "name", "")
        extension = Path(filename).suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            result.errors.append("Unsupported file type. Upload a CSV, XLS, or XLSX file.")
            return result

        content = statement_file.read() if hasattr(statement_file, "read") else statement_file
        if isinstance(content, str):
            content = content.encode()
        result.file_hash = hashlib.sha256(content).hexdigest()

        try:
            frame = self._read_frame(content, extension)
        except Exception as exc:
            result.errors.append(f"Failed to parse statement file: {exc}")
            return result

        if frame.empty:
            result.errors.append("Statement file has no rows")
            return result

        frame.columns = [str(column).strip() for column in frame.columns]
        for index, raw_row in frame.iterrows():
            normalized = self._normalize_row(
                account=account,
                config=config,
                institution=institution,
                source_file_hash=result.file_hash,
                statement_period=statement_period,
                row_number=int(index) + 2,
                raw_row={str(key).strip(): value for key, value in raw_row.to_dict().items()},
            )
            if normalized is None:
                result.invalid_count += 1
                continue
            result.rows.append(normalized)

        result.parsed_count = len(result.rows)
        if not result.rows and not result.errors:
            result.errors.append("No valid statement rows found")
        return result

    def _read_frame(self, content: bytes, extension: str) -> pd.DataFrame:
        if extension == ".csv":
            try:
                return pd.read_csv(io.BytesIO(content), dtype=str).dropna(how="all")
            except UnicodeDecodeError:
                return pd.read_csv(io.BytesIO(content), dtype=str, encoding="latin-1").dropna(how="all")
        return pd.read_excel(io.BytesIO(content), dtype=str).dropna(how="all")

    def _normalize_row(
        self,
        account: FinancialAccount,
        config: dict[str, Any],
        institution: str,
        source_file_hash: str,
        statement_period: str,
        row_number: int,
        raw_row: dict[str, Any],
    ) -> NormalizedStatementRow | None:
        date_value = self._first_value(raw_row, config["date"])
        description = self._first_value(raw_row, config["description"])
        amount_value = self._first_value(raw_row, config["amount"])
        debit_value = self._first_value(raw_row, config.get("debit", []))
        credit_value = self._first_value(raw_row, config.get("credit", []))

        posted_date = self._parse_date(date_value)
        amount, transaction_type = self._parse_amount(amount_value, debit_value, credit_value, account)
        if posted_date is None or amount is None or not description:
            return None

        activity_type = self._first_value(raw_row, config.get("activity", []))
        symbol = self._first_value(raw_row, config.get("symbol", []))
        quantity = self._first_value(raw_row, config.get("quantity", []))
        description = self._normalize_description(description)
        row_hash_base = self._row_hash_base(
            account.id,
            posted_date,
            amount,
            description,
            activity_type,
            symbol,
            quantity,
        )
        row_hash = hashlib.sha256(row_hash_base.encode()).hexdigest()

        return NormalizedStatementRow(
            row_number=row_number,
            posted_date=posted_date,
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            institution=institution,
            source_file_hash=source_file_hash,
            source_row_hash=row_hash,
            source_row_hash_base=row_hash_base,
            statement_period=statement_period,
            activity_type=activity_type,
            symbol=symbol,
            quantity=quantity,
            raw_data={key: self._stringify_value(value) for key, value in raw_row.items()},
        )

    def _classify_rows(self, account: FinancialAccount, result: StatementImportResult) -> None:
        existing_hashes = self._get_existing_row_hashes(account)
        existing_signatures = self._get_existing_change_signatures(account)
        seen_hashes = set()

        for row in result.rows:
            if row.source_row_hash in seen_hashes:
                row.status = "duplicate"
                result.duplicate_count += 1
                continue
            seen_hashes.add(row.source_row_hash)

            if row.source_row_hash in existing_hashes:
                row.status = "duplicate"
                result.duplicate_count += 1
                continue

            change_signature = f"{account.id}:{row.posted_date}:{self._normalize_description(row.description)}"
            if change_signature in existing_signatures:
                row.status = "possible_changed"
                result.possible_changed_count += 1

    def _get_existing_row_hashes(self, account: FinancialAccount) -> set[str]:
        transactions = Transaction.objects.filter(account=account, sync_source="csv").values(
            "date",
            "amount",
            "description",
            "raw_data",
        )
        hashes = set()
        for transaction in transactions:
            raw_data = transaction.get("raw_data") or {}
            source_row_hash = raw_data.get("source_row_hash")
            if source_row_hash:
                hashes.add(source_row_hash)
                continue

            base = self._row_hash_base(
                account.id,
                transaction["date"],
                transaction["amount"],
                transaction["description"],
            )
            hashes.add(hashlib.sha256(base.encode()).hexdigest())
            old_key = f"{account.id}:{transaction['date']}:{transaction['amount']}:{transaction['description']}"
            hashes.add(hashlib.md5(old_key.encode()).hexdigest())
        return hashes

    def _get_existing_change_signatures(self, account: FinancialAccount) -> set[str]:
        transactions = Transaction.objects.filter(account=account, sync_source="csv").values_list(
            "date",
            "description",
        )
        return {
            f"{account.id}:{transaction_date}:{self._normalize_description(description)}"
            for transaction_date, description in transactions
        }

    def _row_hash_base(
        self,
        account_id: int,
        posted_date: date,
        amount: Decimal,
        description: str,
        activity_type: str = "",
        symbol: str = "",
        quantity: str = "",
    ) -> str:
        return ":".join(
            [
                str(account_id),
                posted_date.isoformat(),
                str(abs(Decimal(str(amount))).quantize(Decimal("0.01"))),
                self._normalize_description(description),
                activity_type.strip().lower(),
                symbol.strip().upper(),
                quantity.strip(),
            ]
        )

    def _parse_date(self, value: str) -> date | None:
        if not value:
            return None
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()

    def _parse_amount(
        self,
        amount_value: str,
        debit_value: str,
        credit_value: str,
        account: FinancialAccount,
    ) -> tuple[Decimal | None, str]:
        if debit_value:
            amount = self._decimal(debit_value)
            return amount, "debit"
        if credit_value:
            amount = self._decimal(credit_value)
            return amount, "credit"

        signed_amount = self._signed_decimal(amount_value)
        amount = abs(signed_amount) if signed_amount is not None else None
        if amount is None:
            return None, "debit"
        if signed_amount < 0:
            return abs(amount), "debit"

        # Credit card exports often use positive amounts for purchases.
        if account.account_type == "credit_card":
            return amount, "debit"
        return amount, "credit"

    def _decimal(self, value: str) -> Decimal | None:
        if not value:
            return None
        cleaned = value.replace("$", "").replace(",", "").replace("(", "-").replace(")", "").strip()
        if cleaned in {"", "-", "--"}:
            return None
        try:
            return abs(Decimal(cleaned)).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None

    def _signed_decimal(self, value: str) -> Decimal | None:
        if not value:
            return None
        cleaned = value.replace("$", "").replace(",", "").replace("(", "-").replace(")", "").strip()
        if cleaned in {"", "-", "--"}:
            return None
        try:
            return Decimal(cleaned).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None

    def _first_value(self, raw_row: dict[str, Any], candidates: list[str]) -> str:
        lower_map = {key.strip().lower(): key for key in raw_row}
        for candidate in candidates:
            raw_key = lower_map.get(candidate.strip().lower())
            if raw_key is None:
                continue
            value = self._stringify_value(raw_row.get(raw_key))
            if value:
                return value
        return ""

    def _stringify_value(self, value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    def _normalize_description(self, description: str) -> str:
        return " ".join(str(description).split())
