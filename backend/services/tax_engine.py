"""VAT Tax Calculation Engine for Philippine BIR forms.

Supports BIR 2550M (Monthly VAT) as MVP, designed to extend to:
- BIR 2550Q (Quarterly VAT)
- BIR 1701 (Individual Income Tax)
- BIR 1702 (Corporate Income Tax)
- BIR 2316 (Employee Tax Certificate)
- BIR 1601C (Monthly Withholding Tax)
- SAWT (Summary Alphalist of Withholding Taxes)
"""

from decimal import Decimal
from typing import Any

# Standard VAT rate in Philippines
VAT_RATE = Decimal("0.12")

# BIR form type registry - extensible for future tax types
SUPPORTED_FORMS = {
    "BIR_2550M": {
        "name": "Monthly Value-Added Tax Declaration",
        "frequency": "monthly",
        "fields": [
            "vatable_sales",
            "vat_exempt_sales",
            "zero_rated_sales",
            "output_vat",
            "input_vat_goods",
            "input_vat_services",
            "input_vat_capital",
            "total_input_vat",
            "vat_payable",
            "tax_credit",
            "net_vat_payable",
        ],
    },
    "BIR_2550Q": {
        "name": "Quarterly Value-Added Tax Return",
        "frequency": "quarterly",
        "fields": [],  # TODO: Phase 2
    },
    "BIR_1701": {
        "name": "Annual Income Tax Return (Individual)",
        "frequency": "annual",
        "fields": [],  # TODO: Future
    },
    "BIR_1702": {
        "name": "Annual Income Tax Return (Corporate)",
        "frequency": "annual",
        "fields": [],  # TODO: Future
    },
    "BIR_2316": {
        "name": "Certificate of Compensation Payment/Tax Withheld",
        "frequency": "annual",
        "fields": [],  # TODO: Future
    },
    "BIR_1601C": {
        "name": "Monthly Remittance Return of Income Taxes Withheld",
        "frequency": "monthly",
        "fields": [],  # TODO: Future
    },
    "SAWT": {
        "name": "Summary Alphalist of Withholding Taxes",
        "frequency": "attachment",
        "fields": [],  # TODO: Future
    },
}


def calculate_bir_2550m(sales_data: list[dict], purchases_data: list[dict]) -> dict[str, Any]:
    """Calculate BIR 2550M (Monthly VAT) from sales and purchase records."""
    vatable_sales = Decimal("0")
    vat_exempt_sales = Decimal("0")
    zero_rated_sales = Decimal("0")

    for row in sales_data:
        amount = Decimal(str(row.get("amount", 0)))
        vat_type = row.get("vat_type", "vatable")
        if vat_type == "vatable":
            vatable_sales += amount
        elif vat_type == "exempt":
            vat_exempt_sales += amount
        elif vat_type == "zero_rated":
            zero_rated_sales += amount

    output_vat = vatable_sales * VAT_RATE

    input_vat_goods = Decimal("0")
    input_vat_services = Decimal("0")
    input_vat_capital = Decimal("0")

    for row in purchases_data:
        amount = Decimal(str(row.get("amount", 0)))
        vat_amount = Decimal(str(row.get("vat_amount", 0)))
        category = row.get("category", "goods")

        input_vat = vat_amount if vat_amount else amount * VAT_RATE

        if category == "goods":
            input_vat_goods += input_vat
        elif category == "services":
            input_vat_services += input_vat
        elif category == "capital":
            input_vat_capital += input_vat

    total_input_vat = input_vat_goods + input_vat_services + input_vat_capital
    vat_payable = output_vat - total_input_vat
    net_vat_payable = max(vat_payable, Decimal("0"))
    tax_credit = max(-vat_payable, Decimal("0"))

    return {
        "vatable_sales": str(vatable_sales),
        "vat_exempt_sales": str(vat_exempt_sales),
        "zero_rated_sales": str(zero_rated_sales),
        "total_sales": str(vatable_sales + vat_exempt_sales + zero_rated_sales),
        "output_vat": str(output_vat),
        "input_vat_goods": str(input_vat_goods),
        "input_vat_services": str(input_vat_services),
        "input_vat_capital": str(input_vat_capital),
        "total_input_vat": str(total_input_vat),
        "vat_payable": str(vat_payable),
        "tax_credit_carried_forward": str(tax_credit),
        "net_vat_payable": str(net_vat_payable),
    }


def get_supported_forms() -> dict:
    """Return all supported BIR form types."""
    return {k: {"name": v["name"], "frequency": v["frequency"]} for k, v in SUPPORTED_FORMS.items()}
