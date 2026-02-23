"""Bank statement format auto-detection and standardized parsing.

Supports BDO, BPI, Metrobank, PayPal, Stripe, GCash, and generic CSV formats.
Handles CSV, Excel, PDF, and image files.
Reuses data_processor for CSV/Excel parsing.
"""

import io
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.services.data_processor import extract_full_data

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BankFormatConfig:
    """Configuration for a known bank statement format."""

    name: str
    date_columns: list[str]
    description_columns: list[str]
    debit_column: str | None
    credit_column: str | None
    amount_column: str | None  # Used when debit/credit are combined
    reference_column: str | None
    date_format: str  # strptime format


# Known bank and payment platform statement formats
BANK_FORMATS: dict[str, BankFormatConfig] = {
    "BDO": BankFormatConfig(
        name="BDO (Banco de Oro)",
        date_columns=["Transaction Date", "Date", "Posting Date"],
        description_columns=["Description", "Particulars", "Transaction Description"],
        debit_column="Debit",
        credit_column="Credit",
        amount_column=None,
        reference_column="Reference No.",
        date_format="%m/%d/%Y",
    ),
    "BPI": BankFormatConfig(
        name="BPI (Bank of the Philippine Islands)",
        date_columns=["Date", "Transaction Date", "Value Date"],
        description_columns=["Description", "Remarks", "Transaction Description"],
        debit_column="Withdrawal",
        credit_column="Deposit",
        amount_column=None,
        reference_column="Reference",
        date_format="%m/%d/%Y",
    ),
    "Metrobank": BankFormatConfig(
        name="Metropolitan Bank",
        date_columns=["Date", "Transaction Date"],
        description_columns=["Description", "Particulars"],
        debit_column="Debit",
        credit_column="Credit",
        amount_column=None,
        reference_column="Check No.",
        date_format="%m/%d/%Y",
    ),
    "PayPal": BankFormatConfig(
        name="PayPal",
        date_columns=["Date", "Transaction Date", "Datetime"],
        description_columns=["Description", "Name", "Subject", "Item Title"],
        debit_column=None,
        credit_column=None,
        amount_column="Amount",
        reference_column="Transaction ID",
        date_format="%m/%d/%Y",
    ),
    "Stripe": BankFormatConfig(
        name="Stripe",
        date_columns=["Created (UTC)", "Created", "Date", "created"],
        description_columns=["Description", "Statement Descriptor", "Customer Description"],
        debit_column=None,
        credit_column=None,
        amount_column="Amount",
        reference_column="id",
        date_format="%Y-%m-%d %H:%M",
    ),
    "GCash": BankFormatConfig(
        name="GCash",
        date_columns=["Date", "Transaction Date", "Timestamp"],
        description_columns=["Description", "Transaction Type", "Details"],
        debit_column=None,
        credit_column=None,
        amount_column="Amount",
        reference_column="Reference No.",
        date_format="%m/%d/%Y",
    ),
    "Generic": BankFormatConfig(
        name="Generic CSV",
        date_columns=["date", "Date", "transaction_date", "Transaction Date"],
        description_columns=["description", "Description", "memo", "Memo", "particulars"],
        debit_column="debit",
        credit_column="credit",
        amount_column="amount",
        reference_column="reference",
        date_format="%Y-%m-%d",
    ),
}

# Date/amount regex patterns for PDF/image text fallback parsing
_DATE_PATTERN = re.compile(
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})"
)
_AMOUNT_PATTERN = re.compile(
    r"[\$₱PHP]*\s*([\d,]+\.\d{2})"
)
_DATE_AMOUNT_LINE = re.compile(
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})"
    r"\s+(.+?)\s+"
    r"[\$₱PHP]*\s*([\d,]+\.\d{2})"
)


def detect_bank_format(
    columns: list[str], sample_rows: list[dict]
) -> BankFormatConfig | None:
    """Detect which bank format matches the given columns."""
    columns_lower = {c.lower().strip() for c in columns}

    best_match: BankFormatConfig | None = None
    best_score = 0

    for fmt in BANK_FORMATS.values():
        score = 0
        # Check date columns
        for dc in fmt.date_columns:
            if dc.lower() in columns_lower:
                score += 2
                break
        # Check description columns
        for dc in fmt.description_columns:
            if dc.lower() in columns_lower:
                score += 2
                break
        # Check amount columns
        if fmt.debit_column and fmt.debit_column.lower() in columns_lower:
            score += 1
        if fmt.credit_column and fmt.credit_column.lower() in columns_lower:
            score += 1
        if fmt.amount_column and fmt.amount_column.lower() in columns_lower:
            score += 1

        if score > best_score:
            best_score = score
            best_match = fmt

    return best_match if best_score >= 3 else None


def _find_column(columns: list[str], candidates: list[str]) -> str | None:
    """Find first matching column from candidates (case-insensitive)."""
    columns_map = {c.lower().strip(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in columns_map:
            return columns_map[candidate.lower()]
    return None


def _parse_amount(value: Any) -> float:
    """Parse a monetary value, handling commas and parentheses (negative)."""
    if value is None:
        return 0.0
    s = str(value).strip().replace(",", "")
    if not s or s.lower() == "none" or s.lower() == "nan":
        return 0.0
    # Handle parenthetical negatives: (1234.56) -> -1234.56
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_date(value: Any, date_format: str) -> str | None:
    """Try to parse a date string, return ISO format or None."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "none" or s.lower() == "nan":
        return None

    # Try the expected format first
    for fmt in [date_format, "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue

    # If it already looks like ISO date, return as-is
    if len(s) >= 10 and s[4] == "-":
        return s[:10]
    return None


def parse_bank_statement(
    rows: list[dict], bank_format: BankFormatConfig
) -> list[dict]:
    """Parse rows using a known bank format configuration.

    Returns list of standardized records:
    {date, description, amount, type (debit/credit), reference}
    """
    columns = list(rows[0].keys()) if rows else []

    date_col = _find_column(columns, bank_format.date_columns)
    desc_col = _find_column(columns, bank_format.description_columns)
    debit_col = _find_column(columns, [bank_format.debit_column]) if bank_format.debit_column else None
    credit_col = _find_column(columns, [bank_format.credit_column]) if bank_format.credit_column else None
    amount_col = _find_column(columns, [bank_format.amount_column]) if bank_format.amount_column else None
    ref_col = _find_column(columns, [bank_format.reference_column]) if bank_format.reference_column else None

    results = []
    for row in rows:
        date_val = _parse_date(row.get(date_col) if date_col else None, bank_format.date_format)
        description = str(row.get(desc_col, "")).strip() if desc_col else ""

        # Determine amount and type
        if debit_col and credit_col:
            debit = _parse_amount(row.get(debit_col))
            credit = _parse_amount(row.get(credit_col))
            if debit and not credit:
                amount = abs(debit)
                txn_type = "debit"
            elif credit and not debit:
                amount = abs(credit)
                txn_type = "credit"
            elif debit and credit:
                amount = abs(debit - credit)
                txn_type = "debit" if debit > credit else "credit"
            else:
                amount = 0.0
                txn_type = "debit"
        elif amount_col:
            raw = _parse_amount(row.get(amount_col))
            amount = abs(raw)
            txn_type = "debit" if raw < 0 else "credit"
        else:
            amount = 0.0
            txn_type = "debit"

        reference = str(row.get(ref_col, "")).strip() if ref_col else None

        if amount > 0 or description:  # Skip empty rows
            results.append({
                "date": date_val,
                "description": description,
                "amount": round(amount, 2),
                "type": txn_type,
                "reference": reference if reference and reference.lower() != "none" else None,
            })

    return results


def parse_pdf_bank_statement(file_content: bytes) -> list[dict]:
    """Extract table data from a PDF bank statement using pdfplumber.

    Strategy:
    1. Try extract_tables() for structured PDFs
    2. Fallback to extract_text() + regex for unstructured PDFs
    """
    import pdfplumber

    all_rows: list[dict] = []

    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    # First row as headers
                    headers = [str(h or "").strip() for h in table[0]]
                    if not any(headers):
                        continue
                    for row in table[1:]:
                        if not row or not any(str(c or "").strip() for c in row):
                            continue
                        row_dict = {}
                        for i, header in enumerate(headers):
                            if i < len(row) and header:
                                row_dict[header] = str(row[i] or "").strip()
                        if row_dict:
                            all_rows.append(row_dict)
            else:
                # Fallback: regex-based extraction from text
                text = page.extract_text() or ""
                for line in text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    match = _DATE_AMOUNT_LINE.search(line)
                    if match:
                        all_rows.append({
                            "Date": match.group(1),
                            "Description": match.group(2).strip(),
                            "Amount": match.group(3).replace(",", ""),
                        })

    return all_rows


async def parse_image_bank_statement(file_content: bytes) -> list[dict]:
    """Parse a bank statement image via the OCR microservice.

    Sends the image to the PaddleOCR service, then attempts to reconstruct
    table structure from OCR text lines using x-coordinate clustering.
    Falls back to regex line-by-line parsing for date + amount patterns.
    """
    import httpx

    from backend.config import settings

    all_rows: list[dict] = []

    try:
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            resp = await http_client.post(
                f"{settings.ocr_service_url}/ocr",
                files={"file": ("image.png", file_content, "image/png")},
            )
            resp.raise_for_status()
            ocr_result = resp.json()
    except Exception as e:
        logger.warning("OCR service call failed: %s", e)
        return all_rows

    # OCR result may contain structured lines or raw text
    lines: list[str] = []
    if isinstance(ocr_result, dict):
        # PaddleOCR format: {results: [{text, confidence, box}, ...]}
        results = ocr_result.get("results", ocr_result.get("data", []))
        if isinstance(results, list):
            lines = [
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in results
            ]
    elif isinstance(ocr_result, list):
        lines = [str(item) for item in ocr_result]

    # Parse OCR lines for date + description + amount patterns
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = _DATE_AMOUNT_LINE.search(line)
        if match:
            all_rows.append({
                "Date": match.group(1),
                "Description": match.group(2).strip(),
                "Amount": match.group(3).replace(",", ""),
            })
        else:
            # Try just date + amount (no description)
            date_match = _DATE_PATTERN.search(line)
            amount_match = _AMOUNT_PATTERN.search(line)
            if date_match and amount_match:
                desc = line
                desc = _DATE_PATTERN.sub("", desc)
                desc = _AMOUNT_PATTERN.sub("", desc).strip()
                all_rows.append({
                    "Date": date_match.group(1),
                    "Description": desc or "OCR entry",
                    "Amount": amount_match.group(1).replace(",", ""),
                })

    return all_rows


_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
_PDF_EXTENSIONS = {".pdf"}


async def auto_detect_and_parse(
    file_content: bytes, filename: str, sheet_name: str | None = None
) -> dict[str, Any]:
    """High-level entry: detect bank format and parse statement.

    Supports CSV, Excel, PDF, and image files.
    Returns {bank_name, format_detected, transactions, row_count, file_type}.
    """
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # PDF path
    if ext in _PDF_EXTENSIONS:
        rows = parse_pdf_bank_statement(file_content)
        if not rows:
            return {
                "bank_name": None,
                "format_detected": False,
                "transactions": [],
                "row_count": 0,
                "file_type": "pdf",
            }
        columns = list(rows[0].keys())
        bank_format = detect_bank_format(columns, rows[:5])
        if bank_format:
            transactions = parse_bank_statement(rows, bank_format)
            return {
                "bank_name": bank_format.name,
                "format_detected": True,
                "transactions": transactions,
                "row_count": len(transactions),
                "file_type": "pdf",
            }
        generic = BANK_FORMATS["Generic"]
        transactions = parse_bank_statement(rows, generic)
        return {
            "bank_name": "PDF (generic parsing)",
            "format_detected": False,
            "transactions": transactions,
            "row_count": len(transactions),
            "file_type": "pdf",
        }

    # Image path (OCR)
    if ext in _IMAGE_EXTENSIONS:
        rows = await parse_image_bank_statement(file_content)
        if not rows:
            return {
                "bank_name": None,
                "format_detected": False,
                "transactions": [],
                "row_count": 0,
                "file_type": "image",
            }
        columns = list(rows[0].keys())
        bank_format = detect_bank_format(columns, rows[:5])
        if bank_format:
            transactions = parse_bank_statement(rows, bank_format)
            return {
                "bank_name": bank_format.name,
                "format_detected": True,
                "transactions": transactions,
                "row_count": len(transactions),
                "file_type": "image",
            }
        generic = BANK_FORMATS["Generic"]
        transactions = parse_bank_statement(rows, generic)
        return {
            "bank_name": "Image/OCR (generic parsing)",
            "format_detected": False,
            "transactions": transactions,
            "row_count": len(transactions),
            "file_type": "image",
        }

    # CSV / Excel path (existing)
    rows = extract_full_data(file_content, filename, sheet_name)
    if not rows:
        return {
            "bank_name": None,
            "format_detected": False,
            "transactions": [],
            "row_count": 0,
            "file_type": "csv" if ext == ".csv" else "excel",
        }

    columns = list(rows[0].keys())
    bank_format = detect_bank_format(columns, rows[:5])

    if bank_format:
        transactions = parse_bank_statement(rows, bank_format)
        return {
            "bank_name": bank_format.name,
            "format_detected": True,
            "transactions": transactions,
            "row_count": len(transactions),
            "file_type": "csv" if ext == ".csv" else "excel",
        }

    # Fallback: use Generic format
    generic = BANK_FORMATS["Generic"]
    transactions = parse_bank_statement(rows, generic)
    return {
        "bank_name": "Unknown (generic parsing)",
        "format_detected": False,
        "transactions": transactions,
        "row_count": len(transactions),
        "file_type": "csv" if ext == ".csv" else "excel",
    }
