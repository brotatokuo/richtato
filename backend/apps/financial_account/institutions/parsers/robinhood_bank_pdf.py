"""Parse Robinhood Banking (checking/savings) monthly PDF statements into tabular rows."""

from __future__ import annotations

import io
import re
from datetime import date

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
FULL_TRANSACTION_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(.+?)\s+"
    r"(Credit|Debit)\s+"
    r"([+-])\$([\d,]+\.\d{2})\s+"
    r"\$[\d,]+\.\d{2}$",
    re.IGNORECASE,
)
SPLIT_TRANSACTION_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"(Credit|Debit)\s+"
    r"([+-])\$([\d,]+\.\d{2})\s+"
    r"\$[\d,]+\.\d{2}$",
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
            posted_date, description, _category, sign, amount = full_match.groups()
            if description.strip().lower() in SKIP_DESCRIPTIONS:
                index += 1
                continue
            rows.append(
                _build_row(
                    posted_date=posted_date,
                    description=description.strip(),
                    sign=sign,
                    amount=amount,
                    statement_year=statement_year,
                    account_hint=account_hint,
                )
            )
            index += 1
            continue

        split_match = SPLIT_TRANSACTION_RE.match(line)
        if split_match:
            posted_date, _category, sign, amount = split_match.groups()
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
