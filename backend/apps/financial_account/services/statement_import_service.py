"""CSV/Excel-first statement import service with institution adapters."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from apps.financial_account.models import FinancialAccount
from apps.transaction.models import Transaction

OPENING_BALANCE_DESCRIPTION = "Opening Balance"
BOFA_BANKING_ACCOUNT_TYPES = {"checking", "savings"}
BOFA_MAX_RUNNING_BALANCE_WARNINGS = 3
BOFA_BEGINNING_BALANCE_RE = re.compile(
    r"beginning balance as of (\d{1,2}/\d{1,2}/\d{4})",
    re.IGNORECASE,
)
BOFA_ENDING_BALANCE_RE = re.compile(
    r"ending balance as of (\d{1,2}/\d{1,2}/\d{4})",
    re.IGNORECASE,
)
BOFA_TRANSACTION_DATE_PREFIX = re.compile(r"^\d{2}/\d{2}/\d{4},")
BOFA_EMPTY_AMOUNT_ROW = re.compile(r'^(.+?),,("(?:-)?[\d,]+\.\d{2}")\s*$')
BOFA_AMOUNT_BALANCE_SUFFIX = re.compile(r'^(.+),("(?:-)?[\d,]+\.\d{2}"),("(?:-)?[\d,]+\.\d{2}")\s*$')

INSTITUTION_PARSER_ALIASES = {
    "citibank": "citi",
}

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
    "citi": {
        "display_name": "Citi",
        "domains": ["credit_card"],
        "date": ["Date", "Transaction Date"],
        "description": ["Description"],
        "amount": ["Amount"],
        "debit": ["Debit"],
        "credit": ["Credit"],
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
    balance_summary: dict[str, str] | None = None
    reconciliation: dict[str, Any] = field(default_factory=dict)
    reconciliation_warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Serialize the import result for API responses."""
        payload: dict[str, Any] = {
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
            "reconciliation": self.reconciliation,
            "reconciliation_warnings": list(dict.fromkeys(self.reconciliation_warnings)),
        }
        if self.balance_summary is not None:
            payload["balance_summary"] = self.balance_summary
        return payload


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
        self._validate_bofa_banking_balances(account, institution, result)
        self._plan_opening_balance(account, result)
        return result

    def import_statement(
        self,
        account: FinancialAccount,
        statement_file,
        institution: str,
        statement_period: str = "",
        statement_status: str = "provisional",
        *,
        apply_opening_balance: bool = False,
    ) -> StatementImportResult:
        """Parse, deduplicate, and create transactions for new statement rows."""
        result = self.preview_statement(account, statement_file, institution, statement_period, statement_status)

        if apply_opening_balance:
            self._apply_opening_balance(account, result)
            result.reconciliation["opening_balance_applied"] = True
        else:
            result.reconciliation["opening_balance_applied"] = False

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
        self._reconcile_account_ending_balance(account, result, apply_opening_balance=apply_opening_balance)
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
        institution = INSTITUTION_PARSER_ALIASES.get(institution, institution)
        result.institution = institution
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
        result._raw_content = content  # noqa: SLF001 — used for BoFA balance validation

        try:
            frame = self._read_frame(content, extension, institution=institution)
        except Exception as exc:
            result.errors.append(f"Failed to parse statement file: {exc}")
            return result

        if frame.empty:
            result.errors.append("Statement file has no rows")
            return result

        result._transaction_frame = frame  # noqa: SLF001 — used for BoFA running-balance validation

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

    def _read_frame(self, content: bytes, extension: str, *, institution: str = "") -> pd.DataFrame:
        if extension == ".csv":
            csv_content = content
            if institution == "bofa" or self._looks_like_bofa_banking_csv(content):
                csv_content = self._extract_bofa_transaction_csv(content)
            try:
                return self._read_csv_bytes(csv_content)
            except pd.errors.ParserError:
                if csv_content is content:
                    csv_content = self._extract_bofa_transaction_csv(content)
                    return self._read_csv_bytes(csv_content)
                raise
        return pd.read_excel(io.BytesIO(content), dtype=str).dropna(how="all")

    @staticmethod
    def _read_csv_bytes(csv_content: bytes) -> pd.DataFrame:
        try:
            return pd.read_csv(io.BytesIO(csv_content), dtype=str).dropna(how="all")
        except UnicodeDecodeError:
            return pd.read_csv(
                io.BytesIO(csv_content),
                dtype=str,
                encoding="latin-1",
            ).dropna(how="all")

    @staticmethod
    def _looks_like_bofa_banking_csv(content: bytes) -> bool:
        """Detect BoFA checking/savings CSV exports by summary block or transaction header."""
        text = content.decode("utf-8-sig", errors="replace")
        if "description,,summary amt." in text.lower():
            return True

        for line in text.splitlines():
            normalized = line.strip().lower()
            if normalized.startswith("date,") and "description" in normalized and "amount" in normalized:
                return True
        return False

    def _extract_bofa_transaction_csv(self, content: bytes) -> bytes:
        """Skip BoFA's summary preamble and return only the transaction table CSV.

        Bank-agent downloads often begin with a summary block::

            Description,,Summary Amt.
            Beginning balance as of ...
            ...
            Date,Description,Amount,Running Bal.
            05/13/2026,...

        Pandas cannot parse the mixed column counts unless we start at the
        ``Date,Description,Amount`` header row.
        """
        text = content.decode("utf-8-sig", errors="replace")
        lines = text.splitlines()
        header_idx = None
        for index, line in enumerate(lines):
            normalized = line.strip().lower()
            if not normalized.startswith("date,"):
                continue
            if "description" in normalized and "amount" in normalized:
                header_idx = index
                break

        if header_idx is None:
            return content

        sanitized_lines = [lines[header_idx]]
        for line in lines[header_idx + 1 :]:
            sanitized_lines.append(self._sanitize_bofa_transaction_line(line))

        return "\n".join(sanitized_lines).encode("utf-8")

    @staticmethod
    def _sanitize_bofa_transaction_line(line: str) -> str:
        """Re-quote BoFA rows whose Zelle memos contain unescaped inner quotes."""
        if not BOFA_TRANSACTION_DATE_PREFIX.match(line):
            return line

        date, rest = line.split(",", 1)
        empty_amount_match = BOFA_EMPTY_AMOUNT_ROW.match(rest)
        if empty_amount_match:
            description = StatementImportService._strip_csv_outer_quotes(empty_amount_match.group(1))
            balance = empty_amount_match.group(2)
            return f'{date},"{StatementImportService._csv_escape(description)}",,{balance}'

        amount_balance_match = BOFA_AMOUNT_BALANCE_SUFFIX.match(rest)
        if not amount_balance_match:
            return line

        description = StatementImportService._strip_csv_outer_quotes(amount_balance_match.group(1))
        amount = amount_balance_match.group(2)
        balance = amount_balance_match.group(3)
        return f'{date},"{StatementImportService._csv_escape(description)}",{amount},{balance}'

    @staticmethod
    def _strip_csv_outer_quotes(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1]
        return value

    @staticmethod
    def _csv_escape(value: str) -> str:
        return value.replace('"', '""')

    def _uses_bofa_banking_balances(self, account: FinancialAccount, institution: str) -> bool:
        return institution == "bofa" and account.account_type in BOFA_BANKING_ACCOUNT_TYPES

    def _parse_bofa_balance_summary(self, content: bytes) -> dict[str, str] | None:
        """Extract beginning/ending balances from BoFA's summary preamble."""
        text = content.decode("utf-8-sig", errors="replace")
        beginning_date = None
        beginning_balance = None
        ending_date = None
        ending_balance = None

        for line in text.splitlines():
            normalized = line.strip()
            if not normalized:
                continue
            lower = normalized.lower()
            try:
                cells = next(csv.reader([normalized]))
            except csv.Error:
                continue
            amount_text = cells[-1].strip().strip('"') if cells else ""

            if lower.startswith("beginning balance as of"):
                match = BOFA_BEGINNING_BALANCE_RE.search(lower)
                if match:
                    beginning_date = self._parse_date(match.group(1))
                beginning_balance = self._signed_decimal(amount_text)
            elif lower.startswith("ending balance as of"):
                match = BOFA_ENDING_BALANCE_RE.search(lower)
                if match:
                    ending_date = self._parse_date(match.group(1))
                ending_balance = self._signed_decimal(amount_text)

        if beginning_balance is None or ending_balance is None:
            return None

        summary = {
            "beginning_balance": str(beginning_balance.quantize(Decimal("0.01"))),
            "ending_balance": str(ending_balance.quantize(Decimal("0.01"))),
        }
        if beginning_date is not None:
            summary["beginning_date"] = beginning_date.isoformat()
        if ending_date is not None:
            summary["ending_date"] = ending_date.isoformat()
        return summary

    def _correct_bofa_summary_from_transactions(
        self,
        summary: dict[str, str],
        frame: pd.DataFrame,
    ) -> dict[str, str]:
        """Prefer transaction-table balances when the summary preamble was misparsed."""
        corrected = dict(summary)

        for _, raw_row in frame.iterrows():
            raw_mapping = {str(key).strip(): value for key, value in raw_row.to_dict().items()}
            description = self._first_value(raw_mapping, ["Description", "Payee"])
            if "beginning balance" not in description.lower():
                continue
            running_balance = self._signed_decimal(
                self._first_value(raw_mapping, ["Running Bal.", "Running Bal", "Running Balance"])
            )
            if running_balance is None:
                break
            parsed_beginning = Decimal(corrected["beginning_balance"])
            if abs(running_balance - parsed_beginning) > Decimal("0.01"):
                corrected["beginning_balance"] = str(running_balance.quantize(Decimal("0.01")))
            break

        return corrected

    def _validate_bofa_banking_balances(
        self,
        account: FinancialAccount,
        institution: str,
        result: StatementImportResult,
    ) -> None:
        if not self._uses_bofa_banking_balances(account, institution):
            return

        raw_content = getattr(result, "_raw_content", None)
        frame = getattr(result, "_transaction_frame", None)
        if raw_content is None or frame is None:
            return

        summary = self._parse_bofa_balance_summary(raw_content)
        if summary is None:
            result.reconciliation_warnings.append(
                "Could not read beginning and ending balances from this BoFA statement."
            )
            return

        summary = self._correct_bofa_summary_from_transactions(summary, frame)
        result.balance_summary = summary
        beginning_balance = Decimal(summary["beginning_balance"])
        ending_balance = Decimal(summary["ending_balance"])

        net_activity = Decimal("0")
        for row in result.rows:
            signed = row.amount if row.transaction_type == "credit" else -row.amount
            net_activity += signed

        computed_ending = (beginning_balance + net_activity).quantize(Decimal("0.01"))
        result.reconciliation["computed_ending_balance"] = str(computed_ending)
        result.reconciliation["statement_ending_balance"] = summary["ending_balance"]
        result.reconciliation["net_activity"] = str(net_activity.quantize(Decimal("0.01")))

        if computed_ending != ending_balance:
            discrepancy = (computed_ending - ending_balance).quantize(Decimal("0.01"))
            result.reconciliation["statement_internal_ok"] = False
            result.reconciliation["statement_internal_discrepancy"] = str(discrepancy)
            result.reconciliation_warnings.append(
                "Statement totals are inconsistent: beginning balance "
                f"({beginning_balance}) plus imported activity ({net_activity}) "
                f"equals {computed_ending}, but the statement ending balance is {ending_balance}."
            )
        else:
            result.reconciliation["statement_internal_ok"] = True

        running_errors = self._validate_bofa_running_balances(frame, beginning_balance)
        if running_errors:
            result.reconciliation["running_balance_errors"] = running_errors
            result.reconciliation_warnings.extend(running_errors)

    def _validate_bofa_running_balances(
        self,
        frame: pd.DataFrame,
        beginning_balance: Decimal,
    ) -> list[str]:
        errors: list[str] = []
        expected = beginning_balance

        for index, raw_row in frame.iterrows():
            row_number = int(index) + 2
            raw_mapping = {str(key).strip(): value for key, value in raw_row.to_dict().items()}
            amount_value = self._first_value(raw_mapping, ["Amount"])
            running_value = self._first_value(
                raw_mapping,
                ["Running Bal.", "Running Bal", "Running Balance"],
            )
            signed_amount = self._signed_decimal(amount_value)

            if signed_amount is None:
                if running_value:
                    running_balance = self._signed_decimal(running_value)
                    if running_balance is not None:
                        if abs(running_balance - expected) > Decimal("0.01"):
                            errors.append(
                                f"Row {row_number}: running balance is {running_balance}, "
                                f"expected {expected.quantize(Decimal('0.01'))}."
                            )
                        expected = running_balance
                continue

            expected = (expected + signed_amount).quantize(Decimal("0.01"))
            if not running_value:
                continue

            running_balance = self._signed_decimal(running_value)
            if running_balance is None:
                continue
            if abs(running_balance - expected) > Decimal("0.01"):
                errors.append(
                    f"Row {row_number}: running balance is {running_balance}, "
                    f"expected {expected} after applying the transaction amount."
                )

        if len(errors) > BOFA_MAX_RUNNING_BALANCE_WARNINGS:
            extra = len(errors) - BOFA_MAX_RUNNING_BALANCE_WARNINGS
            return errors[:BOFA_MAX_RUNNING_BALANCE_WARNINGS] + [
                f"... and {extra} more running balance mismatch{'es' if extra != 1 else ''}."
            ]

        return errors

    def _plan_opening_balance(
        self,
        account: FinancialAccount,
        result: StatementImportResult,
    ) -> None:
        if result.balance_summary is None:
            result.reconciliation["opening_balance_action"] = "none"
            return

        beginning_balance = Decimal(result.balance_summary["beginning_balance"])
        beginning_date_text = result.balance_summary.get("beginning_date")
        beginning_date = date.fromisoformat(beginning_date_text) if beginning_date_text else date.today()
        result.reconciliation.update(
            self._build_opening_balance_reconciliation_info(
                account=account,
                beginning_balance=beginning_balance,
                beginning_date=beginning_date,
                for_commit=False,
            )
        )

    def _apply_opening_balance(
        self,
        account: FinancialAccount,
        result: StatementImportResult,
    ) -> None:
        if result.balance_summary is None:
            return

        beginning_balance = Decimal(result.balance_summary["beginning_balance"])
        beginning_date_text = result.balance_summary.get("beginning_date")
        beginning_date = date.fromisoformat(beginning_date_text) if beginning_date_text else date.today()
        result.reconciliation.update(
            self._build_opening_balance_reconciliation_info(
                account=account,
                beginning_balance=beginning_balance,
                beginning_date=beginning_date,
                for_commit=True,
            )
        )

    def _build_opening_balance_reconciliation_info(
        self,
        account: FinancialAccount,
        beginning_balance: Decimal,
        beginning_date: date,
        *,
        for_commit: bool,
    ) -> dict[str, str]:
        existing = Transaction.objects.filter(
            account=account,
            description=OPENING_BALANCE_DESCRIPTION,
        ).first()

        target_type = "credit" if beginning_balance >= 0 else "debit"
        target_amount = abs(beginning_balance).quantize(Decimal("0.01"))
        target_signed = target_amount if target_type == "credit" else -target_amount
        statement_balance_text = str(beginning_balance.quantize(Decimal("0.01")))

        info: dict[str, str] = {
            "statement_beginning_balance": statement_balance_text,
            "statement_beginning_date": beginning_date.isoformat(),
            "opening_balance_amount": statement_balance_text,
            "opening_balance_date": beginning_date.isoformat(),
        }

        if existing is None:
            info["opening_balance_action"] = "create" if for_commit else "available_create"
            if for_commit:
                Transaction.objects.create(
                    user=account.user,
                    account=account,
                    date=beginning_date,
                    amount=target_amount,
                    transaction_type=target_type,
                    description=OPENING_BALANCE_DESCRIPTION,
                    sync_source="manual",
                    status="reconciled",
                )
            return info

        existing_signed = existing.signed_amount
        info["account_opening_balance_current"] = str(existing_signed.quantize(Decimal("0.01")))
        info["account_opening_balance_date_current"] = existing.date.isoformat()
        info["opening_balance_previous_amount"] = str(existing_signed.quantize(Decimal("0.01")))

        if existing_signed == target_signed and existing.date == beginning_date:
            info["opening_balance_action"] = "matched"
            return info

        info["opening_balance_action"] = "update" if for_commit else "available_update"
        if for_commit:
            existing.date = beginning_date
            existing.amount = target_amount
            existing.transaction_type = target_type
            existing.save(update_fields=["date", "amount", "transaction_type", "updated_at"])
        return info

    def _reconcile_account_ending_balance(
        self,
        account: FinancialAccount,
        result: StatementImportResult,
        *,
        apply_opening_balance: bool = False,
    ) -> None:
        if result.balance_summary is None:
            return

        account.refresh_from_db(fields=["balance"])
        ending_balance = Decimal(result.balance_summary["ending_balance"])
        discrepancy = (account.balance - ending_balance).quantize(Decimal("0.01"))

        result.reconciliation["account_balance"] = str(account.balance.quantize(Decimal("0.01")))
        result.reconciliation["account_ending_discrepancy"] = str(discrepancy)

        if discrepancy != Decimal("0"):
            result.reconciliation["account_ending_ok"] = False
            message = (
                "Account balance after import is "
                f"{account.balance.quantize(Decimal('0.01'))}, but the statement ending balance is "
                f"{ending_balance.quantize(Decimal('0.01'))} "
                f"(difference {discrepancy})."
            )
            if not apply_opening_balance:
                message += (
                    " The account opening balance was not changed during import, so a difference here may be expected."
                )
            else:
                message += " Other transactions or skipped duplicates may explain this."
            result.reconciliation_warnings.append(message)
        else:
            result.reconciliation["account_ending_ok"] = True

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
