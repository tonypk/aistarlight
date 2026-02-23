"""Receipt parser: rule-based extraction + confidence gating + LLM fallback.

Layer 1: Regex/dictionary rules for TIN, dates, amounts, VAT type, receipt number.
Layer 2: GPT-4.1 mini for ambiguous fields only (vendor category, unclear VAT).
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

from backend.core.llm import chat_completion

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.85
LLM_AMOUNT_THRESHOLD = 0.70


@dataclass
class ParsedField:
    value: str | float | None = None
    confidence: float = 0.0


@dataclass
class ParsedReceipt:
    vendor_name: ParsedField = field(default_factory=ParsedField)
    tin: ParsedField = field(default_factory=ParsedField)
    date: ParsedField = field(default_factory=ParsedField)
    total_amount: ParsedField = field(default_factory=ParsedField)
    vatable_sales: ParsedField = field(default_factory=ParsedField)
    vat_amount: ParsedField = field(default_factory=ParsedField)
    vat_type: ParsedField = field(default_factory=ParsedField)
    category: ParsedField = field(default_factory=ParsedField)
    receipt_number: ParsedField = field(default_factory=ParsedField)


# ---------- TIN ----------

TIN_PATTERN = re.compile(r"\b(\d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{3,4})\b")


def _extract_tin(text: str) -> ParsedField:
    match = TIN_PATTERN.search(text)
    if match:
        raw = match.group(1)
        digits = re.sub(r"[^0-9]", "", raw)
        if 12 <= len(digits) <= 13:
            formatted = f"{digits[:3]}-{digits[3:6]}-{digits[6:9]}-{digits[9:]}"
            return ParsedField(value=formatted, confidence=0.95)
    return ParsedField()


# ---------- Date ----------

DATE_PATTERNS = [
    # MM/DD/YYYY or MM-DD-YYYY
    (re.compile(r"\b(0?[1-9]|1[0-2])[/\-](0?[1-9]|[12]\d|3[01])[/\-](20\d{2})\b"), "MDY"),
    # YYYY-MM-DD
    (re.compile(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b"), "YMD"),
    # Month DD, YYYY (e.g., "Jan 15, 2024")
    (re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+"
        r"(\d{1,2}),?\s+(20\d{2})\b",
        re.IGNORECASE,
    ), "NAMED"),
    # DD Month YYYY (e.g., "15 January 2024")
    (re.compile(
        r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(20\d{2})\b",
        re.IGNORECASE,
    ), "DNAMED"),
]

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _extract_date(text: str) -> ParsedField:
    for pattern, fmt in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        try:
            if fmt == "MDY":
                m, d, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif fmt == "YMD":
                y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif fmt == "NAMED":
                m = MONTH_MAP.get(match.group(1)[:3].lower(), 0)
                d, y = int(match.group(2)), int(match.group(3))
            elif fmt == "DNAMED":
                d = int(match.group(1))
                m = MONTH_MAP.get(match.group(2)[:3].lower(), 0)
                y = int(match.group(3))
            else:
                continue
            dt = datetime(y, m, d)
            return ParsedField(value=dt.strftime("%Y-%m-%d"), confidence=0.90)
        except (ValueError, KeyError):
            continue
    return ParsedField()


# ---------- Amounts ----------

AMOUNT_PATTERN = re.compile(
    r"(?:₱|PHP|PhP|Php|P)\s*([\d,]+\.\d{2})\b"
)
AMOUNT_LABEL_PATTERNS = [
    (re.compile(r"(?:TOTAL|GRAND\s*TOTAL|AMOUNT\s*DUE|NET\s*AMOUNT)[:\s]*(?:₱|PHP|PhP|Php|P)?\s*([\d,]+\.\d{2})", re.IGNORECASE), "total"),
    (re.compile(r"(?:VATABLE\s*SALES?|VAT[- ]?ABLE)[:\s]*(?:₱|PHP|PhP|Php|P)?\s*([\d,]+\.\d{2})", re.IGNORECASE), "vatable_sales"),
    (re.compile(r"(?:VAT\s*(?:AMOUNT|12%)|12%?\s*VAT|OUTPUT\s*VAT)[:\s]*(?:₱|PHP|PhP|Php|P)?\s*([\d,]+\.\d{2})", re.IGNORECASE), "vat_amount"),
    (re.compile(r"(?:VAT[- ]?EXEMPT\s*SALES?|EXEMPT\s*SALES?)[:\s]*(?:₱|PHP|PhP|Php|P)?\s*([\d,]+\.\d{2})", re.IGNORECASE), "exempt_sales"),
    (re.compile(r"(?:ZERO[- ]?RATED\s*SALES?)[:\s]*(?:₱|PHP|PhP|Php|P)?\s*([\d,]+\.\d{2})", re.IGNORECASE), "zero_rated_sales"),
]


def _parse_amount(raw: str) -> float:
    return float(raw.replace(",", ""))


def _extract_amounts(text: str) -> dict[str, ParsedField]:
    result = {
        "total_amount": ParsedField(),
        "vatable_sales": ParsedField(),
        "vat_amount": ParsedField(),
    }

    for pattern, label in AMOUNT_LABEL_PATTERNS:
        match = pattern.search(text)
        if match:
            amount = _parse_amount(match.group(1))
            if label == "total":
                result["total_amount"] = ParsedField(value=amount, confidence=0.90)
            elif label == "vatable_sales":
                result["vatable_sales"] = ParsedField(value=amount, confidence=0.90)
            elif label == "vat_amount":
                result["vat_amount"] = ParsedField(value=amount, confidence=0.90)

    # Fallback: if no labeled total found, pick the largest amount
    if result["total_amount"].confidence == 0:
        all_amounts = [_parse_amount(m.group(1)) for m in AMOUNT_PATTERN.finditer(text)]
        if all_amounts:
            max_amount = max(all_amounts)
            confidence = 0.75 if len(all_amounts) > 1 else 0.85
            result["total_amount"] = ParsedField(value=max_amount, confidence=confidence)

    # Cross-validate: vatable_sales + vat_amount ≈ total
    vatable = result["vatable_sales"].value
    vat = result["vat_amount"].value
    total = result["total_amount"].value
    if vatable and vat and total:
        expected = float(vatable) + float(vat)
        if abs(expected - float(total)) <= 1.0:
            # Cross-validation passed — boost confidence
            result["total_amount"] = ParsedField(value=total, confidence=0.95)
            result["vatable_sales"] = ParsedField(value=vatable, confidence=0.95)
            result["vat_amount"] = ParsedField(value=vat, confidence=0.95)

    return result


# ---------- VAT Type ----------

VAT_KEYWORDS = {
    "vatable": ["12% vat", "vatable", "12%vat", "vat 12%", "output vat", "vat amount"],
    "exempt": ["vat exempt", "vat-exempt", "exempt from vat", "non-vat"],
    "zero_rated": ["zero rated", "zero-rated", "0% vat", "zero rate"],
}


def _extract_vat_type(text: str) -> ParsedField:
    text_lower = text.lower()
    for vat_type, keywords in VAT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return ParsedField(value=vat_type, confidence=0.90)
    return ParsedField(value="vatable", confidence=0.50)


# ---------- Receipt Number ----------

RECEIPT_NUMBER_PATTERNS = [
    re.compile(r"(?:OR|O\.R\.)\s*(?:No\.?|#)\s*[:.]?\s*(\d[\d-]{3,})", re.IGNORECASE),
    re.compile(r"(?:Invoice|INV)\s*(?:No\.?|#)\s*[:.]?\s*(\d[\d-]{3,})", re.IGNORECASE),
    re.compile(r"(?:SI|S\.I\.)\s*(?:No\.?|#)\s*[:.]?\s*(\d[\d-]{3,})", re.IGNORECASE),
    re.compile(r"(?:Receipt)\s*(?:No\.?|#)\s*[:.]?\s*(\d[\d-]{3,})", re.IGNORECASE),
]


def _extract_receipt_number(text: str) -> ParsedField:
    for pattern in RECEIPT_NUMBER_PATTERNS:
        match = pattern.search(text)
        if match:
            return ParsedField(value=match.group(1).strip(), confidence=0.90)
    return ParsedField()


# ---------- Vendor Name ----------

def _extract_vendor_name(lines: list[dict]) -> ParsedField:
    """Extract vendor name from first few lines of OCR text (typically business name)."""
    # Skip very short lines and common headers
    skip_words = {"official receipt", "sales invoice", "or no", "tin", "vat", "date"}
    candidates = []
    for line in lines[:5]:
        txt = line.get("text", "").strip()
        if len(txt) < 3 or len(txt) > 80:
            continue
        if any(sw in txt.lower() for sw in skip_words):
            continue
        # Skip lines that look like pure numbers or addresses
        if re.match(r"^[\d\s.,-]+$", txt):
            continue
        candidates.append(txt)

    if candidates:
        return ParsedField(value=candidates[0], confidence=0.70)
    return ParsedField()


# ---------- Main Parser ----------

def parse_receipt(ocr_text: str, ocr_lines: list[dict]) -> ParsedReceipt:
    """Parse a receipt using rule-based extraction.

    Args:
        ocr_text: Full OCR text (lines joined by newline).
        ocr_lines: List of dicts with 'text', 'confidence', 'bbox'.

    Returns:
        ParsedReceipt with confidence scores for each field.
    """
    result = ParsedReceipt()
    result.tin = _extract_tin(ocr_text)
    result.date = _extract_date(ocr_text)
    result.receipt_number = _extract_receipt_number(ocr_text)
    result.vat_type = _extract_vat_type(ocr_text)
    result.vendor_name = _extract_vendor_name(ocr_lines)

    amounts = _extract_amounts(ocr_text)
    result.total_amount = amounts["total_amount"]
    result.vatable_sales = amounts["vatable_sales"]
    result.vat_amount = amounts["vat_amount"]

    # Default category based on vendor (low confidence — LLM should resolve)
    result.category = ParsedField(value="goods", confidence=0.50)

    return result


# ---------- Confidence Gating ----------

def needs_llm(parsed: ParsedReceipt) -> dict:
    """Determine which fields need LLM resolution.

    Returns dict of field_name -> context string for LLM.
    """
    ambiguous: dict[str, str] = {}

    if parsed.category.confidence < CONFIDENCE_THRESHOLD:
        vendor = parsed.vendor_name.value or "unknown"
        ambiguous["category"] = f"vendor: {vendor}"

    if parsed.vat_type.confidence < CONFIDENCE_THRESHOLD:
        ambiguous["vat_type"] = "unclear from receipt text"

    if parsed.total_amount.confidence < LLM_AMOUNT_THRESHOLD:
        ambiguous["total_amount"] = "multiple or unclear amounts"

    if parsed.vendor_name.confidence < 0.60:
        ambiguous["vendor_name"] = "cannot determine vendor name"

    return ambiguous


# ---------- LLM Resolution ----------

LLM_SYSTEM_PROMPT = """You are a Philippine receipt data extraction assistant.
Given OCR text from a receipt, resolve the ambiguous fields listed.

For category: classify as "goods" (physical products, food, supplies) or "services" (utilities, telecom, professional services, rent).
For vat_type: classify as "vatable", "exempt", or "zero_rated".
For vendor_name: extract the business/store name.
For total_amount: determine the final total amount in PHP.

Respond ONLY with valid JSON:
{"category": "goods", "vat_type": "vatable", "vendor_name": "Store Name", "total_amount": 1234.56}
Only include fields that were asked to be resolved."""


async def resolve_ambiguous_fields(
    ocr_text: str,
    ambiguous_fields: dict[str, str],
) -> dict:
    """Use GPT-4.1 mini to resolve ambiguous fields.

    Args:
        ocr_text: Full OCR text.
        ambiguous_fields: Dict of field_name -> context.

    Returns:
        Dict of resolved field_name -> value.
    """
    if not ambiguous_fields:
        return {}

    fields_desc = "\n".join(f"- {k}: {v}" for k, v in ambiguous_fields.items())
    prompt = (
        f"OCR text from receipt:\n```\n{ocr_text[:1500]}\n```\n\n"
        f"Resolve these ambiguous fields:\n{fields_desc}"
    )

    try:
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system=LLM_SYSTEM_PROMPT,
            model="gpt-4.1-mini",
            max_tokens=200,
            temperature=0.1,
        )

        # Extract JSON from response
        start = response.index("{")
        end = response.rindex("}") + 1
        resolved = json.loads(response[start:end])

        # Validate resolved fields
        valid_categories = {"goods", "services", "capital", "imports"}
        valid_vat_types = {"vatable", "exempt", "zero_rated"}

        result = {}
        for key, val in resolved.items():
            if key not in ambiguous_fields:
                continue
            if key == "category" and val in valid_categories:
                result["category"] = val
            elif key == "vat_type" and val in valid_vat_types:
                result["vat_type"] = val
            elif key == "vendor_name" and isinstance(val, str) and val.strip():
                result["vendor_name"] = val.strip()
            elif key == "total_amount":
                try:
                    result["total_amount"] = float(val)
                except (ValueError, TypeError):
                    pass

        logger.info("LLM resolved %d/%d fields", len(result), len(ambiguous_fields))
        return result

    except (ValueError, json.JSONDecodeError, KeyError) as e:
        logger.warning("LLM resolution failed: %s", e)
        return {}
