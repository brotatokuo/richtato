"""Parse American Express Rewards Checking monthly PDF statements into tabular rows."""

from __future__ import annotations

import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import pdfplumber

AMEX_CHECKING_MARKERS = (
    "american express",
    "rewards checking",
    "account activity",
)
STATEMENT_DATE_RE = re.compile(
    r"Statement\s+Date:\s+(\d{1,2}/\d{1,2}/\d{4})",
    re.IGNORECASE,
)
ACCOUNT_HINT_RE = re.compile(
    r"Account\s+Ending:\s+\*(\d{4})",
    re.IGNORECASE,
)
SUMMARY_BEGINNING_RE = re.compile(
    r"Beginning Balance as of (\d{1,2}/\d{1,2}/\d{4})\s+\$([\d,]+\.\d{2})",
    re.IGNORECASE,
)
SUMMARY_ENDING_RE = re.compile(
    r"Ending Balance as of (\d{1,2}/\d{1,2}/\d{4})\s+\$([\d,]+\.\d{2})",
    re.IGNORECASE,
)
TRANSACTION_HEADER_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{4})\s+"
    r"(.+?)\s+"
    r"(\(?-?\$[\d,]+\.\d{2}\)?)\s+"
    r"\$([\d,]+\.\d{2})$",
)
TRANSACTION_START_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{4})\s+(.+)$",
)
AMOUNT_BALANCE_RE = re.compile(
    r"^(\(?-?\$[\d,]+\.\d{2}\)?)\s+\$([\d,]+\.\d{2})$",
)
BALANCE_ONLY_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{4})\s+"
    r"(Beginning Balance|Ending Balance)\s+"
    r"\$([\d,]+\.\d{2})$",
    re.IGNORECASE,
)
DATE_PREFIX_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}\s+")
SKIP_DESCRIPTIONS = {
    "beginning balance",
    "ending balance",
}
SECTION_HEADER_PREFIXES = (
    "date description",
    "account activity",
    "important notice",
)
SKIP_LINE_PREFIXES = (
    "accounts offered by",
    "american express® rewards checking statement",
    "statement date:",
    "statement summary",
    "interest summary",
    "account details",
    "contact us",
    "p. ",
    "24/7 account access",
    "americanexpress.com",
    "membershiprewards.com",
    "to view your point balance",
    "about the membership rewards",
    "visit membershiprewards",
    "p.o. box",
)
CONTINUATION_STOP_PREFIXES = ("continued on next page", "continued on reverse", *SKIP_LINE_PREFIXES)


def parse_amex_checking_pdf(content: bytes) -> pd.DataFrame:
    """Extract AmEx Rewards Checking transactions from a monthly PDF statement."""
    text = _extract_pdf_text(content)
    if not _looks_like_amex_checking(text):
        raise ValueError("File does not look like an American Express Rewards Checking statement PDF.")

    statement_year = _extract_statement_year(text)
    if statement_year is None:
        raise ValueError("Could not find statement date in American Express checking PDF.")

    account_hint = _extract_account_hint(text)
    activity_lines = _extract_activity_lines(text)
    rows = _parse_activity_lines(activity_lines, statement_year=statement_year, account_hint=account_hint)
    if not rows:
        raise ValueError("No transactions found in American Express checking PDF.")

    return pd.DataFrame(rows)


def parse_amex_checking_balance_summary(content: bytes) -> dict[str, str] | None:
    """Extract beginning/ending balances from an AmEx Rewards Checking PDF statement."""
    text = _extract_pdf_text(content)
    if not _looks_like_amex_checking(text):
        return None
    return extract_amex_checking_balance_summary(text)


def extract_amex_checking_balance_summary(text: str) -> dict[str, str] | None:
    """Parse beginning/ending balances from extracted AmEx checking PDF text."""
    beginning_balance = None
    ending_balance = None
    beginning_date = None
    ending_date = None

    beginning_match = SUMMARY_BEGINNING_RE.search(text)
    if beginning_match:
        date_text, amount = beginning_match.groups()
        beginning_balance = _decimal_amount(amount)
        beginning_date = _parse_statement_date(date_text)

    ending_match = SUMMARY_ENDING_RE.search(text)
    if ending_match:
        date_text, amount = ending_match.groups()
        ending_balance = _decimal_amount(amount)
        ending_date = _parse_statement_date(date_text)

    if beginning_balance is None or ending_balance is None:
        for line in _extract_activity_lines(text):
            normalized = " ".join(line.split())
            balance_only = BALANCE_ONLY_RE.match(normalized)
            if not balance_only:
                continue
            posted_date, label, amount = balance_only.groups()
            parsed_amount = _decimal_amount(amount)
            parsed_date = _parse_statement_date(posted_date)
            if label.lower() == "beginning balance" and beginning_balance is None:
                beginning_balance = parsed_amount
                beginning_date = parsed_date
            elif label.lower() == "ending balance" and ending_balance is None:
                ending_balance = parsed_amount
                ending_date = parsed_date

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


def _extract_pdf_text(content: bytes) -> str:
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text)
    return "\n".join(pages)


def _looks_like_amex_checking(text: str) -> bool:
    lowered = text.lower()
    return all(marker in lowered for marker in AMEX_CHECKING_MARKERS)


def _extract_statement_year(text: str) -> int | None:
    match = STATEMENT_DATE_RE.search(text)
    if not match:
        return None
    return _parse_statement_date(match.group(1)).year


def _extract_account_hint(text: str) -> str:
    match = ACCOUNT_HINT_RE.search(text)
    return match.group(1) if match else ""


def _extract_activity_lines(text: str) -> list[str]:
    lines = text.splitlines()
    activity_lines: list[str] = []
    in_activity = False
    skip_until_next_transaction = False

    for line in lines:
        normalized = line.strip()
        if not normalized:
            continue
        lowered = normalized.lower()

        if lowered.startswith("account activity"):
            in_activity = True
            skip_until_next_transaction = False
            continue
        if lowered.startswith("date description credits debits balance"):
            in_activity = True
            skip_until_next_transaction = False
            continue
        if not in_activity:
            continue
        if lowered.startswith("important notice"):
            break
        if lowered.startswith("continued on"):
            skip_until_next_transaction = True
            continue
        if skip_until_next_transaction:
            if DATE_PREFIX_RE.match(normalized):
                skip_until_next_transaction = False
            else:
                continue
        if _should_skip_activity_line(normalized):
            continue
        activity_lines.append(normalized)

    return activity_lines


def _should_stop_continuation(line: str) -> bool:
    lowered = line.lower()
    return any(lowered.startswith(prefix) for prefix in CONTINUATION_STOP_PREFIXES)


def _should_skip_activity_line(line: str) -> bool:
    lowered = line.lower()
    if any(lowered.startswith(prefix) for prefix in SECTION_HEADER_PREFIXES):
        return True
    if any(lowered.startswith(prefix) for prefix in SKIP_LINE_PREFIXES):
        return True
    if "24/7 account access" in lowered or "americanexpress.com" in lowered:
        return True
    if lowered.startswith("total credits this period") or lowered.startswith("total debits this period"):
        return True
    if lowered.startswith("earned period") or lowered.startswith("days in statement period"):
        return True
    if lowered.startswith("interest rate") or lowered.startswith("annual percentage yield"):
        return True
    if lowered.startswith("interest earned this period") or lowered.startswith("interest paid this year"):
        return True
    return False


def _parse_activity_lines(
    lines: list[str],
    *,
    statement_year: int,
    account_hint: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        normalized = " ".join(line.split())

        balance_only = BALANCE_ONLY_RE.match(normalized)
        if balance_only:
            index += 1
            continue

        header_match = TRANSACTION_HEADER_RE.match(normalized)
        if header_match:
            posted_date, description, amount_text, balance = header_match.groups()
            if description.strip().lower() in SKIP_DESCRIPTIONS:
                index += 1
                continue

            continuation_parts: list[str] = []
            index += 1
            while index < len(lines):
                next_line = lines[index].strip()
                if not next_line:
                    index += 1
                    continue
                next_normalized = " ".join(next_line.split())
                if DATE_PREFIX_RE.match(next_normalized):
                    break
                if _should_stop_continuation(next_line):
                    break
                if _should_skip_activity_line(next_line):
                    index += 1
                    continue
                continuation_parts.append(next_normalized)
                index += 1

            full_description = " ".join([description.strip(), *continuation_parts]).strip()
            rows.append(
                _build_row(
                    posted_date=posted_date,
                    description=full_description,
                    amount_text=amount_text,
                    balance=balance,
                    statement_year=statement_year,
                    account_hint=account_hint,
                )
            )
            continue

        start_match = TRANSACTION_START_RE.match(normalized)
        if not start_match:
            index += 1
            continue

        posted_date, description = start_match.groups()
        if description.strip().lower() in SKIP_DESCRIPTIONS:
            index += 1
            continue

        continuation_parts: list[str] = []
        amount_text = ""
        balance = ""
        index += 1
        while index < len(lines):
            next_line = lines[index].strip()
            if not next_line:
                index += 1
                continue

            next_normalized = " ".join(next_line.split())
            if DATE_PREFIX_RE.match(next_normalized):
                break
            if _should_stop_continuation(next_line):
                break
            if _should_skip_activity_line(next_line):
                index += 1
                continue

            amount_balance = AMOUNT_BALANCE_RE.match(next_normalized)
            if amount_balance:
                amount_text, balance = amount_balance.groups()
                index += 1
                break

            continuation_parts.append(next_normalized)
            index += 1

        if not amount_text or not balance:
            continue

        full_description = " ".join([description.strip(), *continuation_parts]).strip()
        rows.append(
            _build_row(
                posted_date=posted_date,
                description=full_description,
                amount_text=amount_text,
                balance=balance,
                statement_year=statement_year,
                account_hint=account_hint,
            )
        )

    return rows


def _build_row(
    *,
    posted_date: str,
    description: str,
    amount_text: str,
    balance: str,
    statement_year: int,
    account_hint: str,
) -> dict[str, str]:
    parsed_date = _parse_statement_date(posted_date, statement_year=statement_year)
    signed_amount = amount_text.replace("$", "").replace(",", "").strip()
    return {
        "Date": parsed_date.isoformat(),
        "Description": description,
        "Amount": signed_amount,
        "Balance": balance.replace(",", "").replace("$", ""),
        "Account Hint": account_hint,
    }


def _parse_statement_date(value: str, *, statement_year: int | None = None) -> date:
    month_str, day_str, year_str = value.split("/")
    month = int(month_str)
    day = int(day_str)
    if len(year_str) == 2:
        year = 2000 + int(year_str)
    else:
        year = int(year_str)
    if year < 100:
        year += 2000
    if statement_year is not None and year != statement_year and abs(year - statement_year) > 1:
        year = statement_year
    return date(year, month, day)


def _decimal_amount(value: str) -> Decimal:
    cleaned = value.replace("$", "").replace(",", "").strip()
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount: {value}") from exc
