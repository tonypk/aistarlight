"""BIR compliance rules engine — deterministic checks for tax report validation.

Each rule is a pure function that takes report data and returns a check result.
Rules are organized by severity: CRITICAL > HIGH > MEDIUM > LOW.
"""

import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

# Tolerance for decimal comparison (PHP 0.50)
DECIMAL_TOLERANCE = Decimal("0.50")


def _d(value: Any) -> Decimal:
    """Safely convert a value to Decimal."""
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _check_result(
    check_id: str,
    check_name: str,
    severity: str,
    passed: bool,
    message: str,
) -> dict:
    return {
        "check_id": check_id,
        "check_name": check_name,
        "severity": severity,
        "passed": passed,
        "message": message,
    }


# ---------- CRITICAL Rules ----------


def check_required_fields(data: dict, report_type: str) -> dict:
    """Rule 1: All mandatory BIR fields must not be null/missing."""
    required_by_type = {
        "BIR_2550M": [
            "line_1_vatable_sales", "line_5_total_sales",
            "line_6_output_vat", "line_6b_total_output_vat",
            "line_11_total_input_vat", "line_16_total_amount_due",
        ],
        "BIR_2550Q": [
            "line_1_vatable_sales", "line_5_total_sales",
            "line_6_output_vat", "line_6b_total_output_vat",
            "line_11_total_input_vat", "line_16_total_amount_due",
        ],
        "BIR_1601C": [
            "line_1_total_compensation", "line_8_taxable_compensation",
            "line_9_tax_withheld", "line_16_total_amount_due",
        ],
        "BIR_0619E": [
            "line_1_total_amount_of_income_payments",
            "line_2_total_taxes_withheld",
            "line_9_total_amount_due",
        ],
    }
    required = required_by_type.get(report_type, required_by_type.get("BIR_2550M", []))
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        return _check_result(
            "REQUIRED_FIELDS", "Required Fields Check", "critical", False,
            f"Missing required fields: {', '.join(missing)}"
        )
    return _check_result(
        "REQUIRED_FIELDS", "Required Fields Check", "critical", True,
        "All required fields present"
    )


def check_cross_field_consistency(data: dict, report_type: str) -> dict:
    """Rule 2: total_sales == vatable + govt + zero + exempt."""
    if report_type not in ("BIR_2550M", "BIR_2550Q"):
        return _check_result(
            "CROSS_FIELD", "Cross-Field Consistency", "critical", True,
            "Not applicable for this form type"
        )
    vatable = _d(data.get("line_1_vatable_sales"))
    govt = _d(data.get("line_2_sales_to_government"))
    zero = _d(data.get("line_3_zero_rated_sales"))
    exempt = _d(data.get("line_4_exempt_sales"))
    total = _d(data.get("line_5_total_sales"))
    expected = vatable + govt + zero + exempt
    diff = abs(total - expected)
    if diff > DECIMAL_TOLERANCE:
        return _check_result(
            "CROSS_FIELD", "Cross-Field Consistency", "critical", False,
            f"Total sales ({total}) != sum of lines 1-4 ({expected}), difference: {diff}"
        )
    return _check_result(
        "CROSS_FIELD", "Cross-Field Consistency", "critical", True,
        "Sales lines sum correctly"
    )


# ---------- HIGH Rules ----------


def check_output_vat_accuracy(data: dict, report_type: str) -> dict:
    """Rule 3: output_vat should equal vatable_sales * 12%."""
    if report_type not in ("BIR_2550M", "BIR_2550Q"):
        return _check_result(
            "OUTPUT_VAT", "Output VAT Accuracy", "high", True,
            "Not applicable for this form type"
        )
    vatable = _d(data.get("line_1_vatable_sales"))
    output_vat = _d(data.get("line_6_output_vat"))
    expected = (vatable * Decimal("0.12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    diff = abs(output_vat - expected)
    if diff > DECIMAL_TOLERANCE:
        return _check_result(
            "OUTPUT_VAT", "Output VAT Accuracy", "high", False,
            f"Output VAT ({output_vat}) != vatable sales ({vatable}) x 12% ({expected})"
        )
    return _check_result(
        "OUTPUT_VAT", "Output VAT Accuracy", "high", True,
        "Output VAT correctly calculated at 12%"
    )


def check_government_vat_rate(data: dict, report_type: str) -> dict:
    """Rule 4: govt_vat should equal govt_sales * 5%."""
    if report_type not in ("BIR_2550M", "BIR_2550Q"):
        return _check_result(
            "GOVT_VAT", "Government VAT Rate", "high", True,
            "Not applicable for this form type"
        )
    govt_sales = _d(data.get("line_2_sales_to_government"))
    govt_vat = _d(data.get("line_6a_output_vat_government"))
    if govt_sales == 0 and govt_vat == 0:
        return _check_result(
            "GOVT_VAT", "Government VAT Rate", "high", True,
            "No government sales reported"
        )
    expected = (govt_sales * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    diff = abs(govt_vat - expected)
    if diff > DECIMAL_TOLERANCE:
        return _check_result(
            "GOVT_VAT", "Government VAT Rate", "high", False,
            f"Govt VAT ({govt_vat}) != govt sales ({govt_sales}) x 5% ({expected})"
        )
    return _check_result(
        "GOVT_VAT", "Government VAT Rate", "high", True,
        "Government VAT correctly calculated at 5%"
    )


def check_amount_ranges(data: dict, report_type: str) -> dict:
    """Rule 5: No single amount should exceed 999,999,999 or be negative."""
    issues = []
    max_amount = Decimal("999999999")
    for key, value in data.items():
        if not key.startswith("line_"):
            continue
        amount = _d(value)
        if amount < 0:
            issues.append(f"{key} is negative ({amount})")
        elif amount > max_amount:
            issues.append(f"{key} exceeds max ({amount})")
    if issues:
        return _check_result(
            "AMOUNT_RANGE", "Amount Range Check", "high", False,
            f"Amount range violations: {'; '.join(issues[:5])}"
        )
    return _check_result(
        "AMOUNT_RANGE", "Amount Range Check", "high", True,
        "All amounts within valid range"
    )


# ---------- MEDIUM Rules ----------


def check_tin_format(data: dict, report_type: str) -> dict:
    """Rule 6: TIN should be XXX-XXX-XXX-XXX format."""
    tin = data.get("tin") or data.get("tin_number") or ""
    if not tin:
        return _check_result(
            "TIN_FORMAT", "TIN Format Validation", "medium", True,
            "No TIN to validate (report-level check)"
        )
    pattern = r"^\d{3}-\d{3}-\d{3}-\d{3}$"
    if not re.match(pattern, tin):
        return _check_result(
            "TIN_FORMAT", "TIN Format Validation", "medium", False,
            f"TIN '{tin}' does not match expected format XXX-XXX-XXX-XXX"
        )
    return _check_result(
        "TIN_FORMAT", "TIN Format Validation", "medium", True,
        "TIN format is valid"
    )


def check_filing_deadline(data: dict, report_type: str) -> dict:
    """Rule 7: Check if filing period suggests the report might be overdue."""
    period = data.get("period", "")
    if not period:
        return _check_result(
            "FILING_DEADLINE", "Filing Deadline Check", "medium", True,
            "No period specified"
        )
    today = date.today()
    try:
        # Period format: "2026-01" or "2026-Q1"
        if "-Q" in period:
            year = int(period.split("-Q")[0])
            quarter = int(period.split("-Q")[1])
            # Quarterly due: 25th day of month following end of quarter
            deadline_month = quarter * 3 + 1
            deadline_year = year if deadline_month <= 12 else year + 1
            if deadline_month > 12:
                deadline_month -= 12
            deadline = date(deadline_year, deadline_month, 25)
        else:
            parts = period.split("-")
            year, month = int(parts[0]), int(parts[1])
            # Monthly VAT: 20th of following month
            # EWT/WHT: 10th of following month
            day = 10 if report_type in ("BIR_1601C", "BIR_0619E") else 20
            next_month = month + 1
            next_year = year
            if next_month > 12:
                next_month = 1
                next_year += 1
            deadline = date(next_year, next_month, day)

        if today > deadline:
            days_late = (today - deadline).days
            return _check_result(
                "FILING_DEADLINE", "Filing Deadline Check", "medium", False,
                f"Report may be overdue by {days_late} days (deadline: {deadline})"
            )
    except (ValueError, IndexError):
        pass

    return _check_result(
        "FILING_DEADLINE", "Filing Deadline Check", "medium", True,
        "Filing appears to be within deadline"
    )


def check_period_over_period_anomaly(
    data: dict, report_type: str, prior_data: dict | None = None
) -> dict:
    """Rule 8: Compare with prior period — flag >50% change."""
    if not prior_data:
        return _check_result(
            "PERIOD_ANOMALY", "Period-over-Period Anomaly", "medium", True,
            "No prior period data available for comparison"
        )

    key = "line_5_total_sales" if report_type in ("BIR_2550M", "BIR_2550Q") else "line_16_total_amount_due"
    current = _d(data.get(key))
    prior = _d(prior_data.get(key))
    if prior == 0:
        return _check_result(
            "PERIOD_ANOMALY", "Period-over-Period Anomaly", "medium", True,
            "Prior period was zero — cannot compute variance"
        )
    change_pct = abs((current - prior) / prior * 100)
    if change_pct > 50:
        direction = "increase" if current > prior else "decrease"
        return _check_result(
            "PERIOD_ANOMALY", "Period-over-Period Anomaly", "medium", False,
            f"{key}: {change_pct:.1f}% {direction} vs prior period "
            f"(current: {current}, prior: {prior})"
        )
    return _check_result(
        "PERIOD_ANOMALY", "Period-over-Period Anomaly", "medium", True,
        f"Variance within 50% threshold ({change_pct:.1f}% change)"
    )


def check_duplicate_report(
    data: dict, report_type: str, existing_reports: list[dict] | None = None
) -> dict:
    """Rule 9: Same type + period should not already exist (unless amendment)."""
    if not existing_reports:
        return _check_result(
            "DUPLICATE_REPORT", "Duplicate Report Check", "medium", True,
            "No existing reports to compare"
        )
    period = data.get("period", "")
    duplicates = [
        r for r in existing_reports
        if r.get("report_type") == report_type
        and r.get("period") == period
        and r.get("status") not in ("archived", "rejected")
    ]
    if len(duplicates) > 1:
        return _check_result(
            "DUPLICATE_REPORT", "Duplicate Report Check", "medium", False,
            f"Found {len(duplicates)} active reports for {report_type} period {period}"
        )
    return _check_result(
        "DUPLICATE_REPORT", "Duplicate Report Check", "medium", True,
        "No duplicate reports found"
    )


# ---------- LOW Rules ----------


def check_capital_goods_threshold(data: dict, report_type: str) -> dict:
    """Rule 10: Capital goods input VAT > PHP 1M should be noted for amortization."""
    if report_type not in ("BIR_2550M", "BIR_2550Q"):
        return _check_result(
            "CAPITAL_THRESHOLD", "Capital Goods Threshold", "low", True,
            "Not applicable for this form type"
        )
    capital = _d(data.get("line_8_input_vat_capital"))
    threshold = Decimal("1000000")
    if capital > threshold:
        return _check_result(
            "CAPITAL_THRESHOLD", "Capital Goods Threshold", "low", False,
            f"Capital goods input VAT ({capital}) > PHP 1,000,000 — "
            "should be amortized over useful life (max 60 months per RR 16-2005)"
        )
    return _check_result(
        "CAPITAL_THRESHOLD", "Capital Goods Threshold", "low", True,
        "Capital goods input VAT within threshold"
    )


def check_zero_filing_warning(data: dict, report_type: str) -> dict:
    """Rule 11: Zero total tax due may be suspicious."""
    key_map = {
        "BIR_2550M": "line_16_total_amount_due",
        "BIR_2550Q": "line_16_total_amount_due",
        "BIR_1601C": "line_16_total_amount_due",
        "BIR_0619E": "line_9_total_amount_due",
    }
    key = key_map.get(report_type, "line_16_total_amount_due")
    total = _d(data.get(key))
    if total == 0:
        return _check_result(
            "ZERO_FILING", "Zero Filing Warning", "low", False,
            "Total amount due is zero — verify this is a valid nil return"
        )
    return _check_result(
        "ZERO_FILING", "Zero Filing Warning", "low", True,
        "Non-zero filing amount"
    )


# ---------- Main runner ----------

ALL_RULES = [
    check_required_fields,
    check_cross_field_consistency,
    check_output_vat_accuracy,
    check_government_vat_rate,
    check_amount_ranges,
    check_tin_format,
    check_filing_deadline,
    check_period_over_period_anomaly,
    check_duplicate_report,
    check_capital_goods_threshold,
    check_zero_filing_warning,
]


def run_all_checks(
    data: dict,
    report_type: str,
    prior_data: dict | None = None,
    existing_reports: list[dict] | None = None,
) -> list[dict]:
    """Run all compliance checks and return results list."""
    results = []
    for rule_fn in ALL_RULES:
        if rule_fn in (check_period_over_period_anomaly,):
            results.append(rule_fn(data, report_type, prior_data))
        elif rule_fn in (check_duplicate_report,):
            results.append(rule_fn(data, report_type, existing_reports))
        else:
            results.append(rule_fn(data, report_type))
    return results
