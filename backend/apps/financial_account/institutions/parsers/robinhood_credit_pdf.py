"""Parse Robinhood Credit Card monthly PDF statements into tabular rows."""

from __future__ import annotations

import io
import re
from datetime import date, datetime

import pandas as pd
import pdfplumber

ROBINHOOD_CREDIT_MARKERS = (
    "credit limit",
    "creditcards@robinhood.com",
    "robinhood credit",
)
CLOSING_DATE_RE = re.compile(
    r"Statement\s*Closing\s*Date\s+([A-Za-z]+)\s*(\d{1,2}),?\s*(\d{4})",
    re.IGNORECASE,
)
ACCOUNT_NUMBER_RE = re.compile(
    r"Account\s*Number:?\s*(?:X+\s*)*(\d{4})",
    re.IGNORECASE,
)
DATE_PREFIX_RE = re.compile(r"^\d{2}/\d{2}$")
REFERENCE_RE = re.compile(r"^[A-Z0-9]+$")
AMOUNT_RE = re.compile(r"^[\d,]+\.\d{2}-?$")
SKIP_LINE_PREFIXES = (
    "tran",
    "date",
    "post",
    "reference number",
    "transaction description",
    "amount",
    "transactions continued",
    "total fees",
    "interest charged",
    "totals ",
    "total interest",
    "your annual percentage rate",
    "type of balance",
    "purchases ",
    "cash advances ",
    "payment options",
    "lost or stolen",
    "daily periodic rates",
    "how we calculate",
    "balance subject",
    "when interest charges",
    "billing rights",
    "credit reporting",
    "questions?",
    "notice:",
    "page ",
    "minimum payment warning",
    "late payment warning",
    "account summary",
    "payment information",
    "account number:",
)
SKIP_DESCRIPTIONS = {
    "interest charge on purchases",
    "interest charge on cash advances",
}


def parse_robinhood_credit_pdf(content: bytes) -> pd.DataFrame:
    """Extract Robinhood Credit Card transactions from a monthly PDF statement."""
    text = _extract_pdf_text(content)
    if not _looks_like_robinhood_credit(text):
        raise ValueError("File does not look like a Robinhood Credit Card statement PDF.")

    closing_date = _extract_closing_date(text)
    if closing_date is None:
        raise ValueError("Could not find Statement Closing Date in Robinhood Credit PDF.")

    account_hint = _extract_account_hint(text)
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        parsed = _parse_transaction_line(line, closing_date=closing_date, account_hint=account_hint)
        if parsed is not None:
            rows.append(parsed)

    if not rows:
        raise ValueError("No transactions found in Robinhood Credit PDF.")

    return pd.DataFrame(rows)


def _extract_pdf_text(content: bytes) -> str:
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text)
    return "\n".join(pages)


def _looks_like_robinhood_credit(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ROBINHOOD_CREDIT_MARKERS)


def _extract_closing_date(text: str) -> date | None:
    match = CLOSING_DATE_RE.search(text)
    if not match:
        return None
    month_name, day, year = match.group(1), int(match.group(2)), int(match.group(3))
    parsed = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
    return parsed.date()


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

    parts = normalized.split()
    if len(parts) < 5:
        return None
    if not DATE_PREFIX_RE.match(parts[0]) or not DATE_PREFIX_RE.match(parts[1]):
        return None
    if not REFERENCE_RE.match(parts[2]):
        return None

    amount_token = parts[-1]
    if not AMOUNT_RE.match(amount_token):
        return None

    description_parts = parts[3:-1]
    if description_parts and description_parts[-1].upper() == "CREDIT":
        description_parts = description_parts[:-1]

    description = " ".join(description_parts).strip()
    if not description or description.lower() in SKIP_DESCRIPTIONS:
        return None

    post_date = _infer_full_date(parts[1], closing_date)
    signed_amount = amount_token.replace(",", "")
    if signed_amount.endswith("-"):
        signed_amount = f"-{signed_amount[:-1]}"

    return {
        "Post Date": post_date.isoformat(),
        "Transaction Description": description,
        "Amount": signed_amount,
        "Reference Number": parts[2],
        "Account Hint": account_hint,
    }


def _infer_full_date(mm_dd: str, closing_date: date) -> date:
    month, day = (int(part) for part in mm_dd.split("/"))
    year = closing_date.year
    if month > closing_date.month:
        year -= 1
    return date(year, month, day)
