"""Generate BIR report PDFs and CSV exports."""

import csv
import io
import os
from typing import Any

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.config import settings


def generate_pdf_report(report_type: str, data: dict[str, Any], tenant_info: dict) -> str:
    """Generate a PDF report and return the file path."""
    tin = tenant_info.get("tin_number", "no_tin")
    filename = f"{report_type}_{data.get('period', 'unknown')}_{tin}.pdf"
    filepath = os.path.join(settings.report_dir, filename)

    if report_type == "BIR_2550M":
        _generate_bir_2550m_pdf(filepath, data, tenant_info)
    elif report_type == "BIR_2550Q":
        _generate_bir_2550q_pdf(filepath, data, tenant_info)
    elif report_type == "BIR_1601C":
        _generate_bir_1601c_pdf(filepath, data, tenant_info)
    elif report_type == "BIR_0619E":
        _generate_bir_0619e_pdf(filepath, data, tenant_info)
    else:
        _generate_generic_pdf(filepath, report_type, data, tenant_info)

    return filepath


# Colors
_HEADER_BG = HexColor("#1e3a5f")
_SECTION_BG = HexColor("#e8edf2")
_LINE_GRAY = HexColor("#cccccc")
_ACCENT = HexColor("#2563eb")


def _draw_section_header(c: canvas.Canvas, y: float, width: float, text: str) -> float:
    """Draw a section header bar. Returns new y position."""
    c.setFillColor(_SECTION_BG)
    c.rect(54, y - 14, width - 108, 18, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(60, y - 10, text)
    return y - 22


def _draw_line_item(
    c: canvas.Canvas,
    y: float,
    width: float,
    line_no: str,
    label: str,
    value: str,
    bold: bool = False,
) -> float:
    """Draw a single line item with line number, label, and right-aligned amount."""
    font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(font, 8)
    c.setFillColor(black)
    if line_no:
        c.drawString(60, y, line_no)
    c.drawString(90, y, label)
    c.drawRightString(width - 60, y, f"PHP {_format_amount(value)}")
    # light separator
    c.setStrokeColor(_LINE_GRAY)
    c.setLineWidth(0.3)
    c.line(54, y - 4, width - 54, y - 4)
    return y - 16


def _generate_bir_2550m_pdf(filepath: str, data: dict, tenant_info: dict) -> None:
    """Generate BIR 2550M Monthly VAT Declaration PDF matching official form layout."""
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # === Title Banner ===
    c.setFillColor(_HEADER_BG)
    c.rect(0, height - 70, width, 70, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 30, "BIR Form No. 2550M")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 48, "Monthly Value-Added Tax Declaration")
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, height - 60, "Republic of the Philippines - Department of Finance - Bureau of Internal Revenue")

    # === Part I: Background Information ===
    y = height - 90
    y = _draw_section_header(c, y, width, "Part I - Background Information")

    c.setFont("Helvetica", 8)
    info = [
        ("TIN", tenant_info.get("tin_number", "")),
        ("RDO Code", tenant_info.get("rdo_code", "")),
        ("Taxpayer's Name / Company", tenant_info.get("company_name", "")),
        ("Taxable Period", data.get("period", "")),
        ("Amendment?", "No"),
    ]
    for label, value in info:
        y -= 14
        c.setFont("Helvetica", 8)
        c.drawString(60, y, f"{label}:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(200, y, str(value))

    # === Part II: Sales / Receipts (Lines 1-5) ===
    y -= 20
    y = _draw_section_header(c, y, width, "Part II - Sales / Receipts")

    y = _draw_line_item(c, y, width, "1", "Vatable Sales / Receipts",
                        data.get("line_1_vatable_sales", data.get("vatable_sales", "0")))
    y = _draw_line_item(c, y, width, "2", "Sales to Government (subject to 5% Final Withholding VAT)",
                        data.get("line_2_sales_to_government", "0"))
    y = _draw_line_item(c, y, width, "3", "Zero-Rated Sales",
                        data.get("line_3_zero_rated_sales", data.get("zero_rated_sales", "0")))
    y = _draw_line_item(c, y, width, "4", "Exempt Sales",
                        data.get("line_4_exempt_sales", data.get("vat_exempt_sales", "0")))
    y = _draw_line_item(c, y, width, "5", "Total Sales / Receipts (Sum of Lines 1 to 4)",
                        data.get("line_5_total_sales", data.get("total_sales", "0")), bold=True)

    # === Part III: Output Tax (Lines 6, 6A, 6B) ===
    y -= 8
    y = _draw_section_header(c, y, width, "Part III - Output Tax")

    y = _draw_line_item(c, y, width, "6", "Output VAT (Line 1 x 12%)",
                        data.get("line_6_output_vat", data.get("output_vat", "0")))
    y = _draw_line_item(c, y, width, "6A", "Output VAT on Sales to Government (Line 2 x 5%)",
                        data.get("line_6a_output_vat_government", "0"))
    y = _draw_line_item(c, y, width, "6B", "Total Output Tax (Line 6 + Line 6A)",
                        data.get("line_6b_total_output_vat", data.get("output_vat", "0")), bold=True)

    # === Part IV: Input Tax (Lines 7-11) ===
    y -= 8
    y = _draw_section_header(c, y, width, "Part IV - Allowable Input Tax")

    y = _draw_line_item(c, y, width, "7", "Input VAT on Domestic Purchases of Goods (other than capital goods)",
                        data.get("line_7_input_vat_goods", data.get("input_vat_goods", "0")))
    y = _draw_line_item(c, y, width, "8", "Input VAT on Domestic Purchases of Capital Goods",
                        data.get("line_8_input_vat_capital", data.get("input_vat_capital", "0")))
    y = _draw_line_item(c, y, width, "9", "Input VAT on Domestic Purchases of Services",
                        data.get("line_9_input_vat_services", data.get("input_vat_services", "0")))
    y = _draw_line_item(c, y, width, "10", "Input VAT on Importation of Goods",
                        data.get("line_10_input_vat_imports", "0"))
    y = _draw_line_item(c, y, width, "11", "Total Input Tax (Sum of Lines 7 to 10)",
                        data.get("line_11_total_input_vat", data.get("total_input_vat", "0")), bold=True)

    # === Part V: Tax Due (Lines 12-16) ===
    y -= 8
    y = _draw_section_header(c, y, width, "Part V - Tax Due")

    y = _draw_line_item(c, y, width, "12", "VAT Payable (Line 6B - Line 11)",
                        data.get("line_12_vat_payable", data.get("vat_payable", "0")))
    y = _draw_line_item(c, y, width, "13", "Less: Tax Credits / Payments",
                        data.get("line_13_less_tax_credits", "0"))
    y = _draw_line_item(c, y, width, "14", "Net VAT Payable (Line 12 - Line 13)",
                        data.get("line_14_net_vat_payable", data.get("net_vat_payable", "0")))
    y = _draw_line_item(c, y, width, "15", "Add: Penalties (Surcharge, Interest, Compromise)",
                        data.get("line_15_add_penalties", "0"))

    # Line 16 - Total Amount Due - highlighted
    y -= 4
    c.setFillColor(HexColor("#f0f4ff"))
    c.rect(54, y - 14, width - 108, 22, fill=1, stroke=0)
    c.setStrokeColor(_ACCENT)
    c.setLineWidth(1)
    c.rect(54, y - 14, width - 108, 22, fill=0, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y - 8, "16")
    c.drawString(90, y - 8, "TOTAL AMOUNT DUE (Line 14 + Line 15)")
    total_due = data.get("line_16_total_amount_due", data.get("net_vat_payable", "0"))
    c.setFillColor(_ACCENT)
    c.drawRightString(width - 60, y - 8, f"PHP {_format_amount(total_due)}")
    y -= 24

    # Tax credit info
    tax_credit = data.get("tax_credit_carried_forward", "0")
    if float(tax_credit or 0) > 0:
        y -= 8
        c.setFillColor(HexColor("#fef3c7"))
        c.rect(54, y - 10, width - 108, 18, fill=1, stroke=0)
        c.setFillColor(HexColor("#92400e"))
        c.setFont("Helvetica", 8)
        c.drawString(60, y - 6, f"Excess Input VAT / Tax Credit Carried Forward to Next Period: PHP {_format_amount(tax_credit)}")
        y -= 20

    # === Compliance Score (if available) ===
    compliance_score = data.get("compliance_score")
    if compliance_score is not None:
        y -= 12
        y = _draw_section_header(c, y, width, "Compliance Validation")
        y -= 2
        score = int(compliance_score)
        if score >= 80:
            score_color = HexColor("#065f46")
            bg_color = HexColor("#d1fae5")
            label = "Compliant"
        elif score >= 60:
            score_color = HexColor("#92400e")
            bg_color = HexColor("#fef3c7")
            label = "Needs Review"
        else:
            score_color = HexColor("#991b1b")
            bg_color = HexColor("#fee2e2")
            label = "Non-Compliant"
        c.setFillColor(bg_color)
        c.rect(54, y - 14, width - 108, 22, fill=1, stroke=0)
        c.setFillColor(score_color)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(60, y - 10, f"Score: {score}/100")
        c.setFont("Helvetica", 9)
        c.drawString(160, y - 10, f"— {label}")
        y -= 28

    # === Notes ===
    y -= 16
    c.setFillColor(black)
    c.setFont("Helvetica", 7)
    notes = [
        "IMPORTANT NOTES:",
        "1. This is a draft computation for review. The official BIR 2550M form must be filed via eBIRForms or eFPS.",
        "2. Sales to Government (Line 2): Subject to 5% final withholding VAT per RR 14-2003.",
        "3. Capital Goods (Line 8): Input VAT on depreciable assets > PHP 1,000,000 should be amortized over useful life (max 60 months).",
        "4. Tax Credits (Line 13): Include creditable withholding VAT, prior period excess credits, and other tax payments.",
        "5. Required Attachments: Summary List of Sales (SLS), Summary List of Purchases (SLP), SAWT if applicable.",
        "6. Filing Deadline: 20th day following the end of each month. Late filing incurs 25% surcharge + 12% annual interest.",
    ]
    for note in notes:
        c.drawString(60, y, note)
        y -= 10

    # Footer
    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(width / 2, 30, "Generated by AIStarlight | This is a draft report for review purposes — not for official filing")

    c.save()


def _generate_bir_1601c_pdf(filepath: str, data: dict, tenant_info: dict) -> None:
    """Generate BIR 1601-C Monthly Withholding Tax on Compensation PDF."""
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # Title Banner
    c.setFillColor(_HEADER_BG)
    c.rect(0, height - 70, width, 70, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 30, "BIR Form No. 1601-C")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 48, "Monthly Remittance Return of Income Taxes Withheld on Compensation")
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, height - 60, "Republic of the Philippines - Department of Finance - Bureau of Internal Revenue")

    # Part I: Background
    y = height - 90
    y = _draw_section_header(c, y, width, "Part I - Background Information")
    c.setFont("Helvetica", 8)
    for label, value in [
        ("TIN", tenant_info.get("tin_number", "")),
        ("RDO Code", tenant_info.get("rdo_code", "")),
        ("Taxpayer's Name / Company", tenant_info.get("company_name", "")),
        ("Taxable Month", data.get("period", "")),
    ]:
        y -= 14
        c.setFont("Helvetica", 8)
        c.drawString(60, y, f"{label}:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(200, y, str(value))

    # Part II: Computation
    y -= 20
    y = _draw_section_header(c, y, width, "Part II - Computation of Tax")
    y = _draw_line_item(c, y, width, "1", "Total Amount of Compensation Paid",
                        data.get("line_1_total_compensation", "0"))
    y = _draw_line_item(c, y, width, "2", "Less: Statutory Minimum Wage / Holiday / OT / NSD",
                        data.get("line_2_statutory_minimum_wage", "0"))
    y = _draw_line_item(c, y, width, "3", "Less: Non-Taxable 13th Month & Benefits (up to PHP 90,000)",
                        data.get("line_3_nontaxable_13th_month", "0"))
    y = _draw_line_item(c, y, width, "4", "Less: De Minimis Benefits",
                        data.get("line_4_nontaxable_deminimis", "0"))
    y = _draw_line_item(c, y, width, "5", "Less: SSS/GSIS/PHIC/HDMF Mandatory Contributions",
                        data.get("line_5_sss_gsis_phic_hdmf", "0"))
    y = _draw_line_item(c, y, width, "6", "Less: Other Non-Taxable Compensation",
                        data.get("line_6_other_nontaxable", "0"))
    y = _draw_line_item(c, y, width, "7", "Total Non-Taxable Compensation (Sum of Lines 2-6)",
                        data.get("line_7_total_nontaxable", "0"), bold=True)
    y = _draw_line_item(c, y, width, "8", "Taxable Compensation (Line 1 - Line 7)",
                        data.get("line_8_taxable_compensation", "0"), bold=True)
    y -= 4
    y = _draw_line_item(c, y, width, "9", "Tax Required to be Withheld (per Withholding Tax Table)",
                        data.get("line_9_tax_withheld", "0"))
    y = _draw_line_item(c, y, width, "10", "Adjustment for Over/Under Withholding",
                        data.get("line_10_adjustment", "0"))
    y = _draw_line_item(c, y, width, "11", "Total Tax to be Remitted (Line 9 + Line 10)",
                        data.get("line_11_total_tax_remitted", "0"), bold=True)

    # Part III: Penalties
    y -= 8
    y = _draw_section_header(c, y, width, "Part III - Penalties")
    y = _draw_line_item(c, y, width, "12", "Surcharge", data.get("line_12_surcharge", "0"))
    y = _draw_line_item(c, y, width, "13", "Interest", data.get("line_13_interest", "0"))
    y = _draw_line_item(c, y, width, "14", "Compromise Penalty", data.get("line_14_compromise", "0"))
    y = _draw_line_item(c, y, width, "15", "Total Penalties (Lines 12 to 14)",
                        data.get("line_15_total_penalties", "0"), bold=True)

    # Line 16 - Total Amount Due - highlighted
    y -= 4
    c.setFillColor(HexColor("#f0f4ff"))
    c.rect(54, y - 14, width - 108, 22, fill=1, stroke=0)
    c.setStrokeColor(_ACCENT)
    c.setLineWidth(1)
    c.rect(54, y - 14, width - 108, 22, fill=0, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y - 8, "16")
    c.drawString(90, y - 8, "TOTAL AMOUNT DUE (Line 11 + Line 15)")
    total_due = data.get("line_16_total_amount_due", "0")
    c.setFillColor(_ACCENT)
    c.drawRightString(width - 60, y - 8, f"PHP {_format_amount(total_due)}")
    y -= 24

    # Notes
    y -= 16
    c.setFillColor(black)
    c.setFont("Helvetica", 7)
    for note in [
        "IMPORTANT NOTES:",
        "1. This is a draft computation. The official BIR 1601-C must be filed via eBIRForms or eFPS.",
        "2. Filing Deadline: 10th day of the month following the month of withholding.",
        "3. Withholding tax on compensation is based on the BIR Withholding Tax Table (RR 11-2018).",
        "4. Minimum wage earners are exempt from income tax. Their compensation should be excluded from Line 8.",
        "5. Annual reconciliation is done via BIR Form 1604-CF (due January 31).",
    ]:
        c.drawString(60, y, note)
        y -= 10

    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(width / 2, 30, "Generated by AIStarlight | Draft report for review purposes")
    c.save()


def _generate_bir_0619e_pdf(filepath: str, data: dict, tenant_info: dict) -> None:
    """Generate BIR 0619-E Monthly EWT Remittance PDF."""
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # Title Banner
    c.setFillColor(_HEADER_BG)
    c.rect(0, height - 70, width, 70, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 30, "BIR Form No. 0619-E")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, height - 48, "Monthly Remittance Form for Creditable Income Taxes Withheld (Expanded)")
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, height - 60, "Republic of the Philippines - Department of Finance - Bureau of Internal Revenue")

    # Part I: Background
    y = height - 90
    y = _draw_section_header(c, y, width, "Part I - Background Information")
    c.setFont("Helvetica", 8)
    for label, value in [
        ("TIN", tenant_info.get("tin_number", "")),
        ("RDO Code", tenant_info.get("rdo_code", "")),
        ("Taxpayer's Name / Company", tenant_info.get("company_name", "")),
        ("For the Month", data.get("period", "")),
    ]:
        y -= 14
        c.setFont("Helvetica", 8)
        c.drawString(60, y, f"{label}:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(200, y, str(value))

    # Part II: Computation
    y -= 20
    y = _draw_section_header(c, y, width, "Part II - Computation of Tax")
    y = _draw_line_item(c, y, width, "1", "Total Amount of Income Payments",
                        data.get("line_1_total_amount_of_income_payments", "0"))
    y = _draw_line_item(c, y, width, "2", "Total Taxes Withheld for the Month",
                        data.get("line_2_total_taxes_withheld", "0"))
    y = _draw_line_item(c, y, width, "3", "Adjustment for Over-Remittance from Previous Month(s)",
                        data.get("line_3_adjustment", "0"))
    y = _draw_line_item(c, y, width, "4", "Tax Still Due (Line 2 - Line 3)",
                        data.get("line_4_tax_still_due", "0"), bold=True)

    # Part III: Penalties
    y -= 8
    y = _draw_section_header(c, y, width, "Part III - Penalties")
    y = _draw_line_item(c, y, width, "5", "Surcharge", data.get("line_5_surcharge", "0"))
    y = _draw_line_item(c, y, width, "6", "Interest", data.get("line_6_interest", "0"))
    y = _draw_line_item(c, y, width, "7", "Compromise Penalty", data.get("line_7_compromise", "0"))
    y = _draw_line_item(c, y, width, "8", "Total Penalties (Lines 5 to 7)",
                        data.get("line_8_total_penalties", "0"), bold=True)

    # Line 9 - Total Amount Due - highlighted
    y -= 4
    c.setFillColor(HexColor("#f0f4ff"))
    c.rect(54, y - 14, width - 108, 22, fill=1, stroke=0)
    c.setStrokeColor(_ACCENT)
    c.setLineWidth(1)
    c.rect(54, y - 14, width - 108, 22, fill=0, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y - 8, "9")
    c.drawString(90, y - 8, "TOTAL AMOUNT DUE (Line 4 + Line 8)")
    total_due = data.get("line_9_total_amount_due", "0")
    c.setFillColor(_ACCENT)
    c.drawRightString(width - 60, y - 8, f"PHP {_format_amount(total_due)}")
    y -= 24

    # Notes
    y -= 16
    c.setFillColor(black)
    c.setFont("Helvetica", 7)
    for note in [
        "IMPORTANT NOTES:",
        "1. This is a draft computation. The official BIR 0619-E must be filed via eBIRForms or eFPS.",
        "2. Filing Deadline: 10th day of the month following the month of withholding.",
        "3. This form is for the first 2 months of each quarter only. For the 3rd month, use BIR 1601-EQ.",
        "4. EWT rates are per RR 2-98 as amended by RR 11-2018 (TRAIN Law).",
        "5. Each payee should receive a BIR Form 2307 certificate by the 20th of the month following the quarter.",
    ]:
        c.drawString(60, y, note)
        y -= 10

    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(width / 2, 30, "Generated by AIStarlight | Draft report for review purposes")
    c.save()


def _generate_generic_pdf(filepath: str, report_type: str, data: dict, tenant_info: dict) -> None:
    """Generic PDF generator for future report types."""
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50, f"BIR Form {report_type.replace('BIR_', '')}")

    y = height - 100
    c.setFont("Helvetica", 10)
    c.drawString(72, y, f"Company: {tenant_info.get('company_name', '')}")
    y -= 15
    c.drawString(72, y, f"TIN: {tenant_info.get('tin_number', '')}")
    y -= 30

    for key, value in data.items():
        c.drawString(72, y, f"{key}: {value}")
        y -= 15
        if y < 72:
            c.showPage()
            y = height - 72

    c.save()


def generate_csv_export(data: dict[str, Any]) -> str:
    """Generate CSV string from report data."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Line", "Field", "Value (PHP)"])
    for key, value in data.items():
        if key.startswith("line_"):
            parts = key.split("_", 2)
            line_no = parts[1] if len(parts) > 1 else ""
            label = parts[2].replace("_", " ").title() if len(parts) > 2 else key
            writer.writerow([line_no, label, value])
    return output.getvalue()


def _generate_bir_2550q_pdf(filepath: str, data: dict, tenant_info: dict) -> None:
    """Generate BIR 2550Q Quarterly VAT Return PDF.

    Same structure as 2550M but with quarterly branding and notes.
    """
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # === Title Banner ===
    c.setFillColor(_HEADER_BG)
    c.rect(0, height - 70, width, 70, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 30, "BIR Form No. 2550Q")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 48, "Quarterly Value-Added Tax Return")
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, height - 60, "Republic of the Philippines - Department of Finance - Bureau of Internal Revenue")

    # === Part I: Background Information ===
    y = height - 90
    y = _draw_section_header(c, y, width, "Part I - Background Information")

    c.setFont("Helvetica", 8)
    info = [
        ("TIN", tenant_info.get("tin_number", "")),
        ("RDO Code", tenant_info.get("rdo_code", "")),
        ("Taxpayer's Name / Company", tenant_info.get("company_name", "")),
        ("Taxable Quarter", data.get("period", "")),
        ("Amendment?", "No"),
    ]
    for label, value in info:
        y -= 14
        c.setFont("Helvetica", 8)
        c.drawString(60, y, f"{label}:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(200, y, str(value))

    # === Part II: Sales / Receipts (Lines 1-5) ===
    y -= 20
    y = _draw_section_header(c, y, width, "Part II - Sales / Receipts (Quarterly)")

    y = _draw_line_item(c, y, width, "1", "Vatable Sales / Receipts",
                        data.get("line_1_vatable_sales", data.get("vatable_sales", "0")))
    y = _draw_line_item(c, y, width, "2", "Sales to Government (subject to 5% Final Withholding VAT)",
                        data.get("line_2_sales_to_government", "0"))
    y = _draw_line_item(c, y, width, "3", "Zero-Rated Sales",
                        data.get("line_3_zero_rated_sales", data.get("zero_rated_sales", "0")))
    y = _draw_line_item(c, y, width, "4", "Exempt Sales",
                        data.get("line_4_exempt_sales", data.get("vat_exempt_sales", "0")))
    y = _draw_line_item(c, y, width, "5", "Total Sales / Receipts (Sum of Lines 1 to 4)",
                        data.get("line_5_total_sales", data.get("total_sales", "0")), bold=True)

    # === Part III: Output Tax ===
    y -= 8
    y = _draw_section_header(c, y, width, "Part III - Output Tax")

    y = _draw_line_item(c, y, width, "6", "Output VAT (Line 1 x 12%)",
                        data.get("line_6_output_vat", data.get("output_vat", "0")))
    y = _draw_line_item(c, y, width, "6A", "Output VAT on Sales to Government (Line 2 x 5%)",
                        data.get("line_6a_output_vat_government", "0"))
    y = _draw_line_item(c, y, width, "6B", "Total Output Tax (Line 6 + Line 6A)",
                        data.get("line_6b_total_output_vat", data.get("output_vat", "0")), bold=True)

    # === Part IV: Input Tax ===
    y -= 8
    y = _draw_section_header(c, y, width, "Part IV - Allowable Input Tax")

    y = _draw_line_item(c, y, width, "7", "Input VAT on Domestic Purchases of Goods",
                        data.get("line_7_input_vat_goods", data.get("input_vat_goods", "0")))
    y = _draw_line_item(c, y, width, "8", "Input VAT on Domestic Purchases of Capital Goods",
                        data.get("line_8_input_vat_capital", data.get("input_vat_capital", "0")))
    y = _draw_line_item(c, y, width, "9", "Input VAT on Domestic Purchases of Services",
                        data.get("line_9_input_vat_services", data.get("input_vat_services", "0")))
    y = _draw_line_item(c, y, width, "10", "Input VAT on Importation of Goods",
                        data.get("line_10_input_vat_imports", "0"))
    y = _draw_line_item(c, y, width, "11", "Total Input Tax (Sum of Lines 7 to 10)",
                        data.get("line_11_total_input_vat", data.get("total_input_vat", "0")), bold=True)

    # === Part V: Tax Due ===
    y -= 8
    y = _draw_section_header(c, y, width, "Part V - Tax Due")

    y = _draw_line_item(c, y, width, "12", "VAT Payable (Line 6B - Line 11)",
                        data.get("line_12_vat_payable", data.get("vat_payable", "0")))
    y = _draw_line_item(c, y, width, "13", "Less: Tax Credits / Payments",
                        data.get("line_13_less_tax_credits", "0"))
    y = _draw_line_item(c, y, width, "14", "Net VAT Payable (Line 12 - Line 13)",
                        data.get("line_14_net_vat_payable", data.get("net_vat_payable", "0")))
    y = _draw_line_item(c, y, width, "15", "Add: Penalties (Surcharge, Interest, Compromise)",
                        data.get("line_15_add_penalties", "0"))

    # Line 16 - Total Amount Due - highlighted
    y -= 4
    c.setFillColor(HexColor("#f0f4ff"))
    c.rect(54, y - 14, width - 108, 22, fill=1, stroke=0)
    c.setStrokeColor(_ACCENT)
    c.setLineWidth(1)
    c.rect(54, y - 14, width - 108, 22, fill=0, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y - 8, "16")
    c.drawString(90, y - 8, "TOTAL AMOUNT DUE (Line 14 + Line 15)")
    total_due = data.get("line_16_total_amount_due", data.get("net_vat_payable", "0"))
    c.setFillColor(_ACCENT)
    c.drawRightString(width - 60, y - 8, f"PHP {_format_amount(total_due)}")
    y -= 24

    # Tax credit info
    tax_credit = data.get("tax_credit_carried_forward", "0")
    if float(tax_credit or 0) > 0:
        y -= 8
        c.setFillColor(HexColor("#fef3c7"))
        c.rect(54, y - 10, width - 108, 18, fill=1, stroke=0)
        c.setFillColor(HexColor("#92400e"))
        c.setFont("Helvetica", 8)
        c.drawString(60, y - 6, f"Excess Input VAT / Tax Credit Carried Forward: PHP {_format_amount(tax_credit)}")
        y -= 20

    # === Notes ===
    y -= 16
    c.setFillColor(black)
    c.setFont("Helvetica", 7)
    notes = [
        "IMPORTANT NOTES:",
        "1. This is a draft computation for review. The official BIR 2550Q form must be filed via eBIRForms or eFPS.",
        "2. Filing Deadline: 25th day following the close of each quarter.",
        "3. Required Attachments: Summary List of Sales (SLS), Summary List of Purchases (SLP), SAWT.",
        "4. Quarterly VAT Return consolidates monthly transactions for the taxable quarter.",
    ]
    for note in notes:
        c.drawString(60, y, note)
        y -= 10

    # Footer
    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(width / 2, 30, "Generated by AIStarlight | This is a draft report for review purposes — not for official filing")
    c.save()


def generate_reconciliation_pdf(
    session_data: dict[str, Any],
    summary: dict[str, Any],
    anomalies: list[dict[str, Any]],
    tenant_info: dict,
) -> str:
    """Generate a professional reconciliation report PDF.

    Includes VAT summary, matching statistics, and anomaly listing.
    Returns the file path.
    """
    period = session_data.get("period", "unknown")
    tin = tenant_info.get("tin_number", "no_tin")
    filename = f"reconciliation_{period}_{tin}.pdf"
    filepath = os.path.join(settings.report_dir, filename)

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # === Title Banner ===
    c.setFillColor(_HEADER_BG)
    c.rect(0, height - 70, width, 70, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 30, "VAT Reconciliation Report")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 48, f"Period: {period}")
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, height - 60, f"Company: {tenant_info.get('company_name', '')} | TIN: {tin}")

    y = height - 90

    # === Session Info ===
    y = _draw_section_header(c, y, width, "Session Information")
    c.setFont("Helvetica", 8)
    y -= 14
    c.drawString(60, y, f"Session ID: {session_data.get('id', '')}")
    y -= 14
    c.drawString(60, y, f"Status: {session_data.get('status', '')}")
    y -= 14
    c.drawString(60, y, f"Files: {len(session_data.get('source_files', []))}")

    # === VAT Summary ===
    y -= 20
    y = _draw_section_header(c, y, width, "VAT Summary")

    vat_items = [
        ("Vatable Sales", summary.get("vatable_sales", "0")),
        ("Sales to Government", summary.get("sales_to_government", "0")),
        ("Zero-Rated Sales", summary.get("zero_rated_sales", "0")),
        ("Exempt Sales", summary.get("vat_exempt_sales", "0")),
        ("Total Sales", summary.get("total_sales", "0")),
        ("Output VAT", summary.get("output_vat", "0")),
        ("Output VAT (Government)", summary.get("output_vat_government", "0")),
        ("Total Output VAT", summary.get("total_output_vat", "0")),
        ("Input VAT (Goods)", summary.get("input_vat_goods", "0")),
        ("Input VAT (Capital)", summary.get("input_vat_capital", "0")),
        ("Input VAT (Services)", summary.get("input_vat_services", "0")),
        ("Input VAT (Imports)", summary.get("input_vat_imports", "0")),
        ("Total Input VAT", summary.get("total_input_vat", "0")),
        ("Net VAT", summary.get("net_vat", "0")),
    ]
    for label, value in vat_items:
        is_total = label.startswith("Total") or label == "Net VAT"
        y = _draw_line_item(c, y, width, "", label, value, bold=is_total)

    # === Match Statistics ===
    recon = session_data.get("reconciliation_result") or {}
    match_stats = recon.get("match_stats", {})
    if match_stats:
        y -= 12
        y = _draw_section_header(c, y, width, "Transaction Matching")
        match_items = [
            ("Matched Pairs", str(match_stats.get("matched_pairs", 0))),
            ("Unmatched Records", str(match_stats.get("unmatched_records", 0))),
            ("Unmatched Bank Entries", str(match_stats.get("unmatched_bank", 0))),
            ("Match Rate", f"{match_stats.get('match_rate', 0) * 100:.1f}%"),
        ]
        for label, value in match_items:
            y -= 14
            c.setFont("Helvetica", 8)
            c.drawString(60, y, f"{label}:")
            c.setFont("Helvetica-Bold", 8)
            c.drawString(250, y, value)

    # === Anomalies ===
    if anomalies:
        y -= 20
        y = _draw_section_header(c, y, width, f"Anomalies ({len(anomalies)} found)")
        for i, anomaly in enumerate(anomalies[:20]):  # Limit to 20
            if y < 80:
                c.showPage()
                y = height - 50
            severity = anomaly.get("severity", "")
            severity_color = {
                "high": HexColor("#ef4444"),
                "medium": HexColor("#f59e0b"),
                "low": HexColor("#6b7280"),
            }.get(severity, black)
            c.setFillColor(severity_color)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(60, y, f"[{severity.upper()}]")
            c.setFillColor(black)
            c.setFont("Helvetica", 7)
            desc = anomaly.get("description", "")[:100]
            c.drawString(105, y, desc)
            status = anomaly.get("status", "")
            c.setFont("Helvetica", 6)
            c.drawRightString(width - 60, y, status)
            y -= 12

    # Footer
    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(width / 2, 30, "Generated by AIStarlight | VAT Reconciliation Report")
    c.save()
    return filepath


def _format_amount(value: str) -> str:
    """Format a numeric string as currency."""
    try:
        num = float(value)
        return f"{num:,.2f}"
    except (ValueError, TypeError):
        return value
