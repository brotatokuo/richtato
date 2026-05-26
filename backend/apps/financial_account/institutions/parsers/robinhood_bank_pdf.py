"""Parse Robinhood Banking (checking/savings) monthly PDF statements into tabular rows."""

from __future__ import annotations

import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
import pdfplumber

ROBINHOOD_BANK_MARKERS = (
    "robinhood banking",
    "coastal community bank",
    "account activity",
)
STATEMENT_PERIOD_RE = re.compile(
    r"Statement\s*Period\s+([A-Za-z]{3})\s+\d{1,2}\s*-\s*[A-Za-z]{3}\s+\d{1,2},?\s*(\d{4})",
    re.IGNORECASE,
)
ACCOUNT_HINT_RE = re.compile(
    r"(?:Joint\s+)?(?:Checking|Savings)\s+(\d{4})",
    re.IGNORECASE,
)
SUMMARY_BEGINNING_RE = re.compile(
    r"Beginning Balance\s*\(([A-Za-z]{3})\s+(\d{1,2}),?\s+(\d{4})\)\s+\$([\d,]+\.\d{2})",
    re.IGNORECASE,
)
SUMMARY_ENDING_RE = re.compile(
    r"Total Ending Balance\s*\(([A-Za-z]{3})\s+(\d{1,2}),?\s+(\d{4})\)\s+\$([\d,]+\.\d{2})",
    re.IGNORECASE,
)
ACTIVITY_BEGINNING_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+Beginning Balance\s+\$([\d,]+\.\d{2})$",
    re.IGNORECASE,
)
ACTIVITY_ENDING_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+Ending Balance\s+\$([\d,]+\.\d{2})$",
    re.IGNORECASE,
)
FULL_TRANSACTION_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(.+?)\s+"
    r"(Credit|Debit)\s+"
    r"([+-])\$([\d,]+\.\d{2})\s+"
    r"\$([\d,]+\.\d{2})$",
    re.IGNORECASE,
)
SPLIT_TRANSACTION_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(Credit|Debit)\s+"
    r"([+-])\$([\d,]+\.\d{2})\s+"
    r"\$([\d,]+\.\d{2})$",
    re.IGNORECASE,
)
SKIP_DESCRIPTIONS = {
    "beginning balance",
    "ending balance",
}
SECTION_HEADER_PREFIXES = (
    "date ",
    "account activity",
    "deposit sweep",
    "error resolution",
    "bank balance",
)


def parse_robinhood_bank_pdf(content: bytes) -> pd.DataFrame:
    """Extract Robinhood Banking transactions from a monthly PDF statement."""
    text = _extract_pdf_text(content)
    if not _looks_like_robinhood_bank(text):
        raise ValueError("File does not look like a Robinhood Banking statement PDF.")

    statement_year = _extract_statement_year(text)
    if statement_year is None:
        raise ValueError("Could not find statement period in Robinhood Banking PDF.")

    account_hint = _extract_account_hint(text)
    activity_lines = _extract_activity_lines(text)
    rows = _parse_activity_lines(activity_lines, statement_year=statement_year, account_hint=account_hint)
    if not rows:
        raise ValueError("No transactions found in Robinhood Banking PDF.")

    return pd.DataFrame(rows)


def parse_robinhood_bank_balance_summary(content: bytes) -> dict[str, str] | None:
    """Extract beginning/ending balances from a Robinhood Banking PDF statement."""
    text = _extract_pdf_text(content)
    if not _looks_like_robinhood_bank(text):
        return None
    return extract_robinhood_bank_balance_summary(text)


def extract_robinhood_bank_balance_summary(text: str) -> dict[str, str] | None:
    """Parse beginning/ending balances from extracted Robinhood Banking PDF text."""
    statement_year = _extract_statement_year(text)
    beginning_balance = None
    ending_balance = None
    beginning_date = None
    ending_date = None

    beginning_match = SUMMARY_BEGINNING_RE.search(text)
    if beginning_match:
        month_name, day, year, amount = beginning_match.groups()
        beginning_balance = _decimal_amount(amount)
        beginning_date = _parse_summary_date(month_name, int(day), int(year))

    ending_match = SUMMARY_ENDING_RE.search(text)
    if ending_match:
        month_name, day, year, amount = ending_match.groups()
        ending_balance = _decimal_amount(amount)
        ending_date = _parse_summary_date(month_name, int(day), int(year))

    if statement_year is not None:
        for line in _extract_activity_lines(text):
            normalized = " ".join(line.split())
            beginning_activity = ACTIVITY_BEGINNING_RE.match(normalized)
            if beginning_activity and beginning_balance is None:
                posted_date, amount = beginning_activity.groups()
                beginning_balance = _decimal_amount(amount)
                beginning_date = _parse_statement_date(posted_date, statement_year)

            ending_activity = ACTIVITY_ENDING_RE.match(normalized)
            if ending_activity and ending_balance is None:
                posted_date, amount = ending_activity.groups()
                ending_balance = _decimal_amount(amount)
                ending_date = _parse_statement_date(posted_date, statement_year)

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


def _looks_like_robinhood_bank(text: str) -> bool:
    lowered = text.lower()
    return all(marker in lowered for marker in ROBINHOOD_BANK_MARKERS)


def _extract_statement_year(text: str) -> int | None:
    match = STATEMENT_PERIOD_RE.search(text)
    if not match:
        return None
    return int(match.group(2))


def _extract_account_hint(text: str) -> str:
    match = ACCOUNT_HINT_RE.search(text)
    return match.group(1) if match else ""


def _extract_activity_lines(text: str) -> list[str]:
    lines = text.splitlines()
    start_idx = None
    for index, line in enumerate(lines):
        if line.strip().lower().startswith("date description"):
            start_idx = index + 1
            break
    if start_idx is None:
        return []

    activity_lines: list[str] = []
    for line in lines[start_idx:]:
        normalized = line.strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered.startswith("deposit sweep") or lowered.startswith("error resolution"):
            break
        if lowered.startswith("robinhood banking services"):
            continue
        activity_lines.append(normalized)
    return activity_lines


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
        lowered = line.lower()

        if any(lowered.startswith(prefix) for prefix in SECTION_HEADER_PREFIXES):
            index += 1
            continue

        full_match = FULL_TRANSACTION_RE.match(line)
        if full_match:
            posted_date, description, _category, sign, amount, balance = full_match.groups()
            if description.strip().lower() in SKIP_DESCRIPTIONS:
                index += 1
                continue
            rows.append(
                _build_row(
                    posted_date=posted_date,
                    description=description.strip(),
                    sign=sign,
                    amount=amount,
                    balance=balance,
                    statement_year=statement_year,
                    account_hint=account_hint,
                )
            )
            index += 1
            continue

        split_match = SPLIT_TRANSACTION_RE.match(line)
        if split_match:
            posted_date, _category, sign, amount, balance = split_match.groups()
            prefix = lines[index - 1].strip() if index > 0 else ""
            suffix = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if prefix.lower().startswith("date "):
                prefix = ""
            if suffix and (
                FULL_TRANSACTION_RE.match(suffix)
                or SPLIT_TRANSACTION_RE.match(suffix)
                or suffix.lower().startswith("robinhood banking")
            ):
                suffix = ""
            description = " ".join(part for part in (prefix, suffix) if part).strip()
            if not description or description.lower() in SKIP_DESCRIPTIONS:
                index += 1
                continue
            rows.append(
                _build_row(
                    posted_date=posted_date,
                    description=description,
                    sign=sign,
                    amount=amount,
                    balance=balance,
                    statement_year=statement_year,
                    account_hint=account_hint,
                )
            )
            index += 2 if suffix else 1
            continue

        index += 1
    return rows


def _build_row(
    *,
    posted_date: str,
    description: str,
    sign: str,
    amount: str,
    balance: str,
    statement_year: int,
    account_hint: str,
) -> dict[str, str]:
    parsed_date = _parse_statement_date(posted_date, statement_year)
    signed_amount = f"{sign}{amount.replace(',', '')}"
    if sign == "+":
        signed_amount = signed_amount[1:]
    return {
        "Date": parsed_date.isoformat(),
        "Description": description,
        "Amount": signed_amount,
        "Balance": balance.replace(",", ""),
        "Account Hint": account_hint,
    }


def _parse_statement_date(value: str, statement_year: int) -> date:
    month_str, day_str, year_str = value.split("/")
    month = int(month_str)
    day = int(day_str)
    if len(year_str) == 2:
        year = 2000 + int(year_str)
    else:
        year = int(year_str)
    if year < 100:
        year += 2000
    if year != statement_year and abs(year - statement_year) > 1:
        year = statement_year
    return date(year, month, day)


def _parse_summary_date(month_name: str, day: int, year: int) -> date:
    parsed = datetime.strptime(f"{month_name} {day} {year}", "%b %d %Y")
    return parsed.date()


def _decimal_amount(value: str) -> Decimal:
    cleaned = value.replace("$", "").replace(",", "").strip()
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount: {value}") from exc
