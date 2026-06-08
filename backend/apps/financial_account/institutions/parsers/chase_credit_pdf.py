"""Parse Chase credit card monthly PDF statements into tabular rows."""

from __future__ import annotations

import io
import re
from datetime import date

import pandas as pd
import pdfplumber

CHASE_CREDIT_MARKERS = (
    "chase mobile",
    "ultimate rewards",
    "cardmember service",
    "chase.com/cardhelp",
)
OPENING_CLOSING_DATE_RE = re.compile(
    r"Opening/Closing Date\s+\d{2}/\d{2}/\d{2}\s*-\s*(\d{2})/(\d{2})/(\d{2})",
    re.IGNORECASE,
)
STATEMENT_DATE_RE = re.compile(
    r"Statement Date:\s*(\d{2})/(\d{2})/(\d{2})",
    re.IGNORECASE,
)
ACCOUNT_NUMBER_RE = re.compile(
    r"Account\s*Number:?\s*(?:X+\s*)*(\d{4})",
    re.IGNORECASE,
)
TRANSACTION_LINE_RE = re.compile(
    r"^(\d{2}/\d{2})\s+(.+)\s+(-?[\d,]*\.\d{2})$",
)
SKIP_LINE_PREFIXES = (
    "date of",
    "transaction merchant",
    "total fees",
    "total interest",
    "page ",
    "annual percentage",
    "purchases ",
    "cash advances",
    "balance transfers",
    "my chase loan",
    "year-to-date",
    "account activity",
    "interest charges",
    "payments and other credits",
    "purchase",
    "fees charged",
    "your autopay",
    "your is the annual",
    "manage your account",
    "opening/closing date",
    "account number:",
    "late payment warning",
    "minimum payment warning",
    "account summary",
    "ultimate rewards",
    "(v) =",
    "(d) =",
    "(a) =",
    "please see information",
    "0000001 fis",
    "x 0000001",
)
SKIP_DESCRIPTIONS = {
    "total fees for this period",
}


def parse_chase_credit_pdf(content: bytes) -> pd.DataFrame:
    """Extract Chase credit card transactions from a monthly PDF statement."""
    text = _extract_pdf_text(content)
    if not _looks_like_chase_credit(text):
        raise ValueError("File does not look like a Chase credit card statement PDF.")

    closing_date = _extract_closing_date(text)
    if closing_date is None:
        raise ValueError("Could not find statement closing date in Chase credit PDF.")

    account_hint = _extract_account_hint(text)
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        parsed = _parse_transaction_line(line, closing_date=closing_date, account_hint=account_hint)
        if parsed is not None:
            rows.append(parsed)

    if not rows:
        raise ValueError("No transactions found in Chase credit PDF.")

    return pd.DataFrame(rows)


def _extract_pdf_text(content: bytes) -> str:
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text)
    return "\n".join(pages)


def _looks_like_chase_credit(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in CHASE_CREDIT_MARKERS)


def _extract_closing_date(text: str) -> date | None:
    match = OPENING_CLOSING_DATE_RE.search(text)
    if match:
        month, day, year_suffix = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return date(2000 + year_suffix, month, day)

    match = STATEMENT_DATE_RE.search(text)
    if match:
        month, day, year_suffix = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return date(2000 + year_suffix, month, day)

    return None


def _extract_account_hint(text: str) -> str:
    match = ACCOUNT_NUMBER_RE.search(text)
    return match.group(1) if match else ""


def _parse_transaction_line(
    line: str,
    *,
    closing_date: date,
    account_hint: str,
) -> dict[str, str] | None:
    normalized = " ".join(line.split())
    if not normalized:
        return None

    lowered = normalized.lower()
    if any(lowered.startswith(prefix) for prefix in SKIP_LINE_PREFIXES):
        return None

    match = TRANSACTION_LINE_RE.match(normalized)
    if not match:
        return None

    mm_dd, description, amount_token = match.group(1), match.group(2).strip(), match.group(3)
    if not description or description.lower() in SKIP_DESCRIPTIONS:
        return None

    posted_date = _infer_full_date(mm_dd, closing_date)
    signed_amount = amount_token.replace(",", "")
    if signed_amount.startswith("."):
        signed_amount = f"0{signed_amount}"

    return {
        "Transaction Date": posted_date.isoformat(),
        "Description": description,
        "Amount": signed_amount,
        "Account Hint": account_hint,
    }


def _infer_full_date(mm_dd: str, closing_date: date) -> date:
    month, day = (int(part) for part in mm_dd.split("/"))
    year = closing_date.year
    if month > closing_date.month:
        year -= 1
    return date(year, month, day)
