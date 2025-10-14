import subprocess
import tempfile
from typing import List, Optional, Tuple

import pandas as pd
import pdfplumber

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None
from PIL import Image, ImageFilter, ImageOps

try:
    import pillow_heif  # Registers HEIF/HEIC plugin for PIL

    pillow_heif.register_heif_opener()
except Exception:
    # If HEIF support is not available, HEIC files won't be supported
    pillow_heif = None


def _has_text_layer(pdf_path: str) -> bool:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                if page.extract_text():
                    return True
            except Exception:
                # If text extraction fails for a page, keep checking others
                continue
    return False


def ocr_pdf_if_needed(src_path: str) -> str:
    """
    Ensure the input PDF has a text layer. If not, run OCR using OCRmyPDF and
    return the path to the searchable PDF. If it already has text, return the
    original path.
    """
    if _has_text_layer(src_path):
        return src_path

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()

    # --skip-text keeps text-only PDFs intact; harmless if already scanned.
    # --quiet reduces noise; rely on exceptions for failures.
    subprocess.run(
        [
            "ocrmypdf",
            "--skip-text",
            "--optimize",
            "0",
            src_path,
            tmp.name,
            "--quiet",
        ],
        check=True,
    )
    return tmp.name


def extract_tables_from_pdf(pdf_path: str) -> pd.DataFrame:
    """
    Extract tables from a (searchable) PDF using pdfplumber and return a raw
    DataFrame of rows. Column naming/cleaning is left to the caller since
    layouts vary by bank.
    """
    rows: List[List[Optional[str]]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables() or []
            except Exception:
                tables = []
            for table in tables:
                for r in table:
                    # Normalize row length using the widest row
                    rows.append([c.strip() if isinstance(c, str) else c for c in r])

    if not rows:
        return pd.DataFrame()

    # Heuristic: use the longest row as header, if it looks like a header row.
    header = max(rows, key=lambda r: len(r))
    num_cols = len(header)
    normalized = []
    for r in rows:
        if len(r) < num_cols:
            r = r + [None] * (num_cols - len(r))
        elif len(r) > num_cols:
            r = r[:num_cols]
        normalized.append(r)

    df = pd.DataFrame(normalized)
    df.columns = [f"col_{i}" for i in range(num_cols)]
    return df


def extract_statement_to_df(path: str) -> pd.DataFrame:
    """
    Entry point for statement extraction. Currently supports PDF via OCRmyPDF +
    pdfplumber. Returns a raw DataFrame best-effort extracted from tables.
    A subsequent canonicalizer should map to [Date, Description, Amount].
    """
    if path.lower().endswith(".pdf"):
        searchable = ocr_pdf_if_needed(path)
        return extract_tables_from_pdf(searchable)

    if path.lower().endswith((".jpg", ".jpeg", ".png", ".heic", ".heif")):
        return extract_image_to_df(path)

    raise ValueError(
        "Unsupported file type for OCR extraction. Supported: PDF, JPG, JPEG, PNG, HEIC/HEIF."
    )


def _parse_amount(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    negative = False
    # Parentheses mean negative
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    s = s.replace("$", "").replace(",", "").replace(" ", "")
    # Handle trailing minus
    if s.endswith("-"):
        negative = True
        s = s[:-1]
    try:
        val = float(s)
        return -val if negative else val
    except Exception:
        return None


def _score_date_column(series: pd.Series) -> int:
    # Try to parse as dates; score by number of successful parses
    try:
        parsed = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
        return int(parsed.notna().sum())
    except Exception:
        return 0


def _score_amount_column(series: pd.Series) -> int:
    try:
        numeric = series.map(_parse_amount)
        return int(pd.Series(numeric).notna().sum())
    except Exception:
        return 0


def map_raw_table_to_standard(raw_df: pd.DataFrame, card_name: str) -> pd.DataFrame:
    """
    Best-effort mapping of a raw OCR-extracted table to the standard schema:
    ['Card', 'Date', 'Description', 'Amount', 'Category'].

    Heuristics:
    - Choose the column with the highest successful date parses as Date.
    - Choose the column with the most parsable monetary values as Amount.
    - Choose the longest non-date/non-amount text column as Description.
    - Set Card to the provided card_name and Category to 'Unknown'.
    """
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(
            columns=["Card", "Date", "Description", "Amount", "Category"]
        )  # empty

    # Ensure string column names
    raw_df = raw_df.copy()
    raw_df.columns = [str(c) for c in raw_df.columns]

    # Identify date and amount columns by scoring
    date_scores: List[Tuple[str, int]] = [
        (c, _score_date_column(raw_df[c])) for c in raw_df.columns
    ]
    amount_scores: List[Tuple[str, int]] = [
        (c, _score_amount_column(raw_df[c])) for c in raw_df.columns
    ]

    date_col = max(date_scores, key=lambda t: t[1])[0] if date_scores else None
    amount_col = max(amount_scores, key=lambda t: t[1])[0] if amount_scores else None

    # Description: choose a column that's not the chosen date/amount, prefer texty
    candidate_desc_cols = [c for c in raw_df.columns if c not in {date_col, amount_col}]
    if candidate_desc_cols:
        # Score by average string length
        def avg_len(series: pd.Series) -> float:
            try:
                s = series.dropna().astype(str)
                if s.empty:
                    return 0.0
                return float(s.map(len).mean())
            except Exception:
                return 0.0

        desc_col = max(candidate_desc_cols, key=lambda c: avg_len(raw_df[c]))
    else:
        desc_col = None

    # Build output
    out = pd.DataFrame()
    # Card
    out["Card"] = card_name

    # Date
    if date_col is not None:
        out["Date"] = pd.to_datetime(raw_df[date_col], errors="coerce").dt.date
    else:
        out["Date"] = pd.NaT

    # Description
    if desc_col is not None:
        out["Description"] = raw_df[desc_col].astype(str)
    else:
        out["Description"] = ""

    # Amount
    if amount_col is not None:
        out["Amount"] = raw_df[amount_col].map(_parse_amount)
    else:
        out["Amount"] = None

    # Category default Unknown (downstream will create if missing)
    out["Category"] = "Unknown"

    # Drop rows where Date or Amount are missing to reduce noise
    out = out.dropna(subset=["Date", "Amount"]).reset_index(drop=True)
    return out


def _open_image_any(path: str) -> Image.Image:
    # HEIC support if pillow-heif installed
    lower = path.lower()
    if lower.endswith((".heic", ".heif")) and pillow_heif is None:
        raise ValueError(
            "HEIC/HEIF not supported: install pillow-heif and system libheif"
        )
    img = Image.open(path)
    return img


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(img)
    # Light denoise/contrast boost
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    return gray


def extract_image_to_df(path: str) -> pd.DataFrame:
    """
    OCR a receipt/statement photo and heuristically extract transaction-like rows
    using line parsing for dates and amounts.
    Returns a DataFrame with generic columns that can be mapped by caller.
    """
    if pytesseract is None:
        raise ImportError(
            "pytesseract is required for image OCR. Install it or avoid image OCR endpoints during setup."
        )

    img = _open_image_any(path)
    proc = _preprocess_for_ocr(img)
    text = pytesseract.image_to_string(proc)

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Heuristics: capture lines containing a date and an amount
    candidates: List[List[Optional[str]]] = []
    for ln in lines:
        # Find date-like token
        date_token = None
        tokens = ln.replace("\t", " ").split()
        for t in tokens:
            # Simple date patterns; pandas will validate later
            if any(ch in t for ch in ["/", "-", "."]):
                date_token = t
                break
        # Find amount-like token
        amount_token = None
        for t in reversed(tokens):
            t_clean = t.replace(",", "").replace("$", "")
            if t_clean.endswith("-"):
                t_clean = t_clean[:-1]
            if t_clean.replace(".", "", 1).isdigit() or (
                t_clean.startswith("(") and t_clean.endswith(")")
            ):
                amount_token = t
                break
        if date_token and amount_token:
            desc = ln
            candidates.append([date_token, desc, amount_token])

    if not candidates:
        return pd.DataFrame()

    df = pd.DataFrame(candidates, columns=["date_col", "desc_col", "amount_col"])
    return df
