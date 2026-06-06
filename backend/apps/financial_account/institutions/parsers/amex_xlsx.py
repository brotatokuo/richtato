"""Parse American Express activity exports (XLS/XLSX)."""

from __future__ import annotations

import io

import pandas as pd

AMEX_ACTIVITY_SHEET = "Transaction Details"
AMEX_HEADER_COLUMNS = ("date", "description", "amount")


def parse_amex_activity_excel(content: bytes) -> pd.DataFrame:
    """Extract transactions from an Amex activity workbook.

    Amex exports begin with account metadata and place the transaction table
    header on row 7 (``Date``, ``Description``, ``Amount``, ...). Plain
    spreadsheets with headers on the first row are also supported.
    """
    buffer = io.BytesIO(content)
    workbook = pd.ExcelFile(buffer)
    sheet_name = _select_sheet(workbook.sheet_names)
    preview = pd.read_excel(
        workbook,
        sheet_name=sheet_name,
        header=None,
        nrows=15,
        dtype=str,
    )
    header_row = _find_header_row(preview)
    if header_row is None:
        frame = pd.read_excel(workbook, sheet_name=sheet_name, dtype=str)
    else:
        frame = pd.read_excel(
            workbook,
            sheet_name=sheet_name,
            header=header_row,
            dtype=str,
        )
    return frame.dropna(how="all")


def _select_sheet(sheet_names: list[str]) -> str:
    if AMEX_ACTIVITY_SHEET in sheet_names:
        return AMEX_ACTIVITY_SHEET
    return sheet_names[0]


def _find_header_row(preview: pd.DataFrame) -> int | None:
    for index, row in preview.iterrows():
        normalized_cells = {
            str(value).strip().lower()
            for value in row.tolist()
            if value is not None and not pd.isna(value) and str(value).strip()
        }
        if all(column in normalized_cells for column in AMEX_HEADER_COLUMNS):
            return int(index)
    return None
