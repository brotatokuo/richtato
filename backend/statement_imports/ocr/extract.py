import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pdfplumber
import pillow_heif
import pytesseract
from PIL import Image, ImageFilter, ImageOps

pillow_heif.register_heif_opener()


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


def _rasterize_pdf_to_images(src_path: str, dpi: int = 300) -> list[str]:
    """
    Render PDF pages to PNG images using pdftoppm (Poppler). Returns a list of
    temporary file paths. Caller is responsible for cleanup if needed.
    """
    import glob
    import os

    tmpdir = tempfile.mkdtemp(prefix="pdfppm_")
    prefix = os.path.join(tmpdir, "page")
    try:
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                f"-r{dpi}",
                src_path,
                prefix,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        # If pdftoppm is unavailable, raise a clear error so the caller can instruct installation
        raise RuntimeError(
            "pdftoppm is required to rasterize PDFs for Tesseract OCR. Install poppler (e.g., 'brew install poppler')."
        ) from exc

    image_paths = sorted(glob.glob(f"{prefix}-*.png"))
    if not image_paths:
        # No pages produced; fail explicitly
        raise RuntimeError("Failed to rasterize PDF to images.")
    return image_paths


def ocr_pdf_if_needed(src_path: str) -> str:
    """
    For statement table extraction pipelines that rely on a text layer, keep
    the previous behavior: ensure a searchable PDF using OCRmyPDF when needed.
    This preserves existing statement import behavior without changing to
    image-based Tesseract parsing.
    """
    if _has_text_layer(src_path):
        return src_path

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()

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
        # Construct as dict of empty lists to satisfy strict type checkers
        return pd.DataFrame(
            {
                "Card": [],
                "Date": [],
                "Description": [],
                "Amount": [],
                "Category": [],
            }
        )  # empty

    # Ensure string column names
    raw_df = raw_df.copy()
    raw_df.columns = [str(c) for c in raw_df.columns]

    # Identify date and amount columns by scoring
    date_scores: List[Tuple[str, int]] = [
        (c, _score_date_column(pd.Series(raw_df[c]))) for c in raw_df.columns
    ]
    amount_scores: List[Tuple[str, int]] = [
        (c, _score_amount_column(pd.Series(raw_df[c]))) for c in raw_df.columns
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

        desc_col = max(candidate_desc_cols, key=lambda c: avg_len(pd.Series(raw_df[c])))
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


class OCRExtractor:
    """
    OCR abstraction with pluggable engines: 'tesseract', 'paddleocr', 'doctr'.
    If engine is None, default order is PaddleOCR -> Tesseract -> docTR.
    """

    def __init__(self, engine: Optional[str] = None):
        self.engine = engine

    def _available_engines(self) -> List[str]:
        engines: List[str] = []
        try:
            if pytesseract is not None:
                engines.append("tesseract")
        except Exception:
            pass
        try:
            # Lazy import to avoid name resolution errors at type-check time
            _ = _get_paddle_ocr()
            if _ is not None:
                engines.append("paddleocr")
        except Exception:
            pass
        try:
            _ = _get_doctr_model()
            if _ is not None:
                engines.append("doctr")
        except Exception:
            pass
        return engines

    def _resolve_engine_order(self) -> List[str]:
        if self.engine:
            ordered = [self.engine]
            ordered.extend([e for e in self._available_engines() if e != self.engine])
            return ordered
        return [
            e
            for e in ["paddleocr", "tesseract", "doctr"]
            if e in self._available_engines()
        ]

    def extract_lines(self, path: str) -> List[str]:
        lower = path.lower()
        if lower.endswith(".pdf"):
            return self._extract_lines_from_pdf(path)
        return self._extract_lines_from_image(path)

    def _extract_lines_from_image(self, path: str) -> List[str]:
        attempts: List[str] = []
        for engine in self._resolve_engine_order():
            try:
                if engine == "tesseract":
                    img = _open_image_any(path)
                    proc = _preprocess_for_ocr(img)
                    text = pytesseract.image_to_string(proc)  # type: ignore[arg-type]
                    return [ln.strip() for ln in text.splitlines() if ln.strip()]
                if engine == "paddleocr":
                    ocr = _get_paddle_ocr()
                    if ocr is None:
                        raise RuntimeError("PaddleOCR unavailable")
                    result = ocr.ocr(path, cls=True)
                    lines: List[str] = []
                    for page in result:
                        for _, (box, (text, conf)) in enumerate(page):
                            if conf is None or conf < 0.5:
                                continue
                            if text:
                                lines.append(str(text).strip())
                    return lines
                if engine == "doctr":
                    model = _get_doctr_model()
                    # Avoid referencing DocumentFile type if unavailable
                    if model is None or DocumentFile is None:  # type: ignore[name-defined]
                        raise RuntimeError("docTR unavailable")
                    doc = DocumentFile.from_images([path])  # type: ignore[name-defined]
                    result = model(doc)
                    lines: List[str] = []
                    for page in result.pages:
                        for block in page.blocks:
                            for line in block.lines:
                                words = [
                                    w.value
                                    for w in line.words
                                    if getattr(w, "value", None)
                                ]
                                if words:
                                    lines.append(" ".join(words).strip())
                    return lines
            except Exception as exc:
                attempts.append(f"{engine}: {exc}")
                continue
        raise ImportError("No OCR engine available. " + ", ".join(attempts))

    def _extract_lines_from_pdf(self, path: str) -> List[str]:
        # Try docTR on PDF if requested/available
        order = self._resolve_engine_order()
        if "doctr" in order:
            try:
                model = _get_doctr_model()
                if model is not None and DocumentFile is not None:  # type: ignore[name-defined]
                    doc = DocumentFile.from_pdf(path)  # type: ignore[name-defined]
                    result = model(doc)
                    lines: List[str] = []
                    for page in result.pages:
                        for block in page.blocks:
                            for line in block.lines:
                                words = [
                                    w.value
                                    for w in line.words
                                    if getattr(w, "value", None)
                                ]
                                if words:
                                    lines.append(" ".join(words).strip())
                    if lines:
                        return lines
            except Exception:
                pass
        # Fallback: rasterize to images and OCR per page
        image_paths = _rasterize_pdf_to_images(path)
        lines: List[str] = []
        for img_path in image_paths:
            try:
                lines.extend(self._extract_lines_from_image(img_path))
            except Exception:
                continue
        return lines


def extract_image_to_df(path: str, engine: Optional[str] = None) -> pd.DataFrame:
    """
    OCR a receipt/statement photo and heuristically extract transaction-like rows
    using line parsing for dates and amounts.
    Returns a DataFrame with generic columns that can be mapped by caller.
    """
    extractor = OCRExtractor(engine=engine)
    lines: List[str] = extractor.extract_lines(path)
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

    # Build DataFrame explicitly as a dict to satisfy strict type checkers
    df = pd.DataFrame(
        {
            "date_col": [row[0] for row in candidates],
            "desc_col": [row[1] for row in candidates],
            "amount_col": [row[2] for row in candidates],
        }
    )
    return df


def extract_receipt_fields(path: str, engine: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract key fields from a receipt image/PDF using the specified OCR engine
    ('tesseract', 'paddleocr', 'doctr'). If not specified, uses a default order.
    """
    extractor = OCRExtractor(engine=engine)
    lines: List[str] = extractor.extract_lines(path)

    import re
    from datetime import date as _date

    import pandas as pd

    # Total amount
    total = None
    for pat in [
        r"total\s*[:\-]?\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
        r"amount\s*due\s*[:\-]?\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
        r"balance\s*due\s*[:\-]?\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
    ]:
        joined = "\n".join(lines)
        m = re.search(pat, joined, flags=re.I)
        if m:
            try:
                total = float(m.group(1))
                break
            except Exception:
                pass

    # Date
    parsed_date = None
    for ln in lines:
        m = re.search(
            r"(\d{4}[\/\-\._]\d{1,2}[\/\-\._]\d{1,2}|\d{1,2}[\/\-\._]\d{1,2}[\/\-\._]\d{2,4})",
            ln,
        )
        if m:
            try:
                parsed_date = str(pd.to_datetime(m.group(1), errors="raise").date())
                break
            except Exception:
                continue
    if parsed_date is None:
        parsed_date = str(_date.today())

    # Merchant: first non-header line
    merchant = None
    for ln in lines[:5]:
        if len(ln) >= 2 and not re.search(
            r"(receipt|invoice|total|tax|amount|date)", ln, re.I
        ):
            merchant = ln
            break

    return {
        "merchant": merchant,
        "date": parsed_date,
        "total": total,
        "raw_lines": lines,
    }
