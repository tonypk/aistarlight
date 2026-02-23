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
# Final withholding VAT rate for sales to government
GOVT_VAT_RATE = Decimal("0.05")

# BIR form type registry - extensible for future tax types
SUPPORTED_FORMS = {
    "BIR_2550M": {
        "name": "Monthly Value-Added Tax Declaration",
        "frequency": "monthly",
        "fields": [
            "vatable_sales",
            "sales_to_government",
            "zero_rated_sales",
            "vat_exempt_sales",
            "total_sales",
            "output_vat",
            "output_vat_government",
            "total_output_vat",
            "input_vat_goods",
            "input_vat_capital",
            "input_vat_services",
            "input_vat_imports",
            "total_input_vat",
            "vat_payable",
            "less_tax_credits",
            "net_vat_payable",
            "add_penalties",
            "total_amount_due",
            "tax_credit_carried_forward",
        ],
    },
    "BIR_2550Q": {
        "name": "Quarterly Value-Added Tax Return",
        "frequency": "quarterly",
        "fields": [
            "vatable_sales",
            "sales_to_government",
            "zero_rated_sales",
            "vat_exempt_sales",
            "total_sales",
            "output_vat",
            "output_vat_government",
            "total_output_vat",
            "input_vat_goods",
            "input_vat_capital",
            "input_vat_services",
            "input_vat_imports",
            "total_input_vat",
            "vat_payable",
            "less_tax_credits",
            "net_vat_payable",
            "add_penalties",
            "total_amount_due",
            "tax_credit_carried_forward",
        ],
    },
    "BIR_1601C": {
        "name": "Monthly Remittance Return of Income Taxes Withheld on Compensation",
        "frequency": "monthly",
        "fields": [
            "line_1_total_compensation",
            "line_2_statutory_minimum_wage",
            "line_3_nontaxable_13th_month",
            "line_4_nontaxable_deminimis",
            "line_5_sss_gsis_phic_hdmf",
            "line_6_other_nontaxable",
            "line_7_total_nontaxable",
            "line_8_taxable_compensation",
            "line_9_tax_withheld",
            "line_10_adjustment",
            "line_11_total_tax_remitted",
            "line_12_surcharge",
            "line_13_interest",
            "line_14_compromise",
            "line_15_total_penalties",
            "line_16_total_amount_due",
        ],
    },
    "BIR_0619E": {
        "name": "Monthly Remittance Form for Creditable Income Taxes Withheld (Expanded)",
        "frequency": "monthly",
        "fields": [
            "line_1_total_amount_of_income_payments",
            "line_2_total_taxes_withheld",
            "line_3_adjustment",
            "line_4_tax_still_due",
            "line_5_surcharge",
            "line_6_interest",
            "line_7_compromise",
            "line_8_total_penalties",
            "line_9_total_amount_due",
        ],
    },
    "BIR_1701": {
        "name": "Annual Income Tax Return (Individual)",
        "frequency": "annual",
        "fields": [],
        "status": "coming_soon",
    },
    "BIR_1702": {
        "name": "Annual Income Tax Return (Corporate)",
        "frequency": "annual",
        "fields": [],
        "status": "coming_soon",
    },
    "BIR_2316": {
        "name": "Certificate of Compensation Payment/Tax Withheld",
        "frequency": "annual",
        "fields": [],
        "status": "coming_soon",
    },
    "SAWT": {
        "name": "Summary Alphalist of Withholding Taxes",
        "frequency": "attachment",
        "fields": [],
        "status": "coming_soon",
    },
}


def calculate_bir_2550m(
    sales_data: list[dict],
    purchases_data: list[dict],
    tax_credits: Decimal | str | None = None,
    penalties: Decimal | str | None = None,
) -> dict[str, Any]:
    """Calculate BIR 2550M (Monthly VAT) from sales and purchase records.

    Follows the actual BIR 2550M form structure:
      Part II  - Sales/Receipts (Lines 1-5)
      Part III - Output Tax (Lines 6, 6A, 6B)
      Part IV  - Input Tax (Lines 7-11)
      Part V   - Tax Due (Lines 12-16)
    """
    # --- Part II: Sales Classification ---
    vatable_sales = Decimal("0")
    sales_to_government = Decimal("0")
    zero_rated_sales = Decimal("0")
    vat_exempt_sales = Decimal("0")

    for row in sales_data:
        amount = Decimal(str(row.get("amount", 0)))
        vat_type = str(row.get("vat_type", "vatable")).lower().strip()
        if vat_type == "government":
            sales_to_government += amount
        elif vat_type == "zero_rated":
            zero_rated_sales += amount
        elif vat_type == "exempt":
            vat_exempt_sales += amount
        else:  # "vatable" or default
            vatable_sales += amount

    total_sales = vatable_sales + sales_to_government + zero_rated_sales + vat_exempt_sales

    # --- Part III: Output Tax ---
    # Line 6: Output VAT on vatable sales (12%)
    output_vat = vatable_sales * VAT_RATE
    # Line 6A: Output VAT on sales to government (5% final withholding)
    output_vat_government = sales_to_government * GOVT_VAT_RATE
    # Line 6B: Total Output Tax
    total_output_vat = output_vat + output_vat_government

    # --- Part IV: Input Tax ---
    input_vat_goods = Decimal("0")
    input_vat_capital = Decimal("0")
    input_vat_services = Decimal("0")
    input_vat_imports = Decimal("0")

    for row in purchases_data:
        amount = Decimal(str(row.get("amount", 0)))
        vat_amount = Decimal(str(row.get("vat_amount", 0)))
        category = str(row.get("category", "goods")).lower().strip()

        input_vat = vat_amount if vat_amount else amount * VAT_RATE

        if category == "capital":
            input_vat_capital += input_vat
        elif category == "services":
            input_vat_services += input_vat
        elif category == "imports":
            input_vat_imports += input_vat
        else:  # "goods" or default
            input_vat_goods += input_vat

    total_input_vat = input_vat_goods + input_vat_capital + input_vat_services + input_vat_imports

    # --- Part V: Tax Due ---
    # Line 12: VAT Payable (Output - Input)
    vat_payable = total_output_vat - total_input_vat

    # Line 13: Less Tax Credits/Payments (from prior periods, etc.)
    less_tax_credits = Decimal(str(tax_credits)) if tax_credits else Decimal("0")

    # Line 14: Net VAT Payable
    net_vat_payable_raw = vat_payable - less_tax_credits
    net_vat_payable = max(net_vat_payable_raw, Decimal("0"))

    # Tax credit carried forward (excess input VAT)
    tax_credit_carried_forward = max(-net_vat_payable_raw, Decimal("0"))

    # Line 15: Add Penalties (25% surcharge + 12% interest if late)
    add_penalties = Decimal(str(penalties)) if penalties else Decimal("0")

    # Line 16: Total Amount Due
    total_amount_due = net_vat_payable + add_penalties

    return {
        # Part II - Sales
        "line_1_vatable_sales": str(vatable_sales),
        "line_2_sales_to_government": str(sales_to_government),
        "line_3_zero_rated_sales": str(zero_rated_sales),
        "line_4_exempt_sales": str(vat_exempt_sales),
        "line_5_total_sales": str(total_sales),
        # Part III - Output Tax
        "line_6_output_vat": str(output_vat),
        "line_6a_output_vat_government": str(output_vat_government),
        "line_6b_total_output_vat": str(total_output_vat),
        # Part IV - Input Tax
        "line_7_input_vat_goods": str(input_vat_goods),
        "line_8_input_vat_capital": str(input_vat_capital),
        "line_9_input_vat_services": str(input_vat_services),
        "line_10_input_vat_imports": str(input_vat_imports),
        "line_11_total_input_vat": str(total_input_vat),
        # Part V - Tax Due
        "line_12_vat_payable": str(vat_payable),
        "line_13_less_tax_credits": str(less_tax_credits),
        "line_14_net_vat_payable": str(net_vat_payable),
        "line_15_add_penalties": str(add_penalties),
        "line_16_total_amount_due": str(total_amount_due),
        # Extra
        "tax_credit_carried_forward": str(tax_credit_carried_forward),
        # Legacy compatibility keys
        "vatable_sales": str(vatable_sales),
        "vat_exempt_sales": str(vat_exempt_sales),
        "zero_rated_sales": str(zero_rated_sales),
        "total_sales": str(total_sales),
        "output_vat": str(output_vat),
        "input_vat_goods": str(input_vat_goods),
        "input_vat_services": str(input_vat_services),
        "input_vat_capital": str(input_vat_capital),
        "total_input_vat": str(total_input_vat),
        "vat_payable": str(vat_payable),
        "net_vat_payable": str(net_vat_payable),
    }


def calculate_bir_2550q(
    sales_data: list[dict],
    purchases_data: list[dict],
    tax_credits: Decimal | str | None = None,
    penalties: Decimal | str | None = None,
) -> dict[str, Any]:
    """Calculate BIR 2550Q (Quarterly VAT) from sales and purchase records.

    The 2550Q structure is nearly identical to 2550M but aggregates quarterly data.
    The calculation logic is the same — only the form metadata and period differ.
    """
    result = calculate_bir_2550m(sales_data, purchases_data, tax_credits, penalties)
    result["form_type"] = "BIR_2550Q"
    return result


def calculate_bir_1601c(
    compensation_data: dict[str, Any],
) -> dict[str, Any]:
    """Calculate BIR 1601-C (Monthly Remittance of Withholding Tax on Compensation).

    Args:
        compensation_data: Dict with keys matching 1601C fields.
    """
    total_comp = Decimal(str(compensation_data.get("total_compensation", 0)))
    min_wage = Decimal(str(compensation_data.get("statutory_minimum_wage", 0)))
    thirteenth = Decimal(str(compensation_data.get("nontaxable_13th_month", 0)))
    deminimis = Decimal(str(compensation_data.get("nontaxable_deminimis", 0)))
    sss_gsis = Decimal(str(compensation_data.get("sss_gsis_phic_hdmf", 0)))
    other_nt = Decimal(str(compensation_data.get("other_nontaxable", 0)))
    tax_withheld = Decimal(str(compensation_data.get("tax_withheld", 0)))
    adjustment = Decimal(str(compensation_data.get("adjustment", 0)))
    surcharge = Decimal(str(compensation_data.get("surcharge", 0)))
    interest = Decimal(str(compensation_data.get("interest", 0)))
    compromise = Decimal(str(compensation_data.get("compromise", 0)))

    total_nontaxable = min_wage + thirteenth + deminimis + sss_gsis + other_nt
    taxable_comp = max(total_comp - total_nontaxable, Decimal("0"))
    total_tax_remitted = tax_withheld + adjustment
    total_penalties = surcharge + interest + compromise
    total_due = total_tax_remitted + total_penalties

    return {
        "line_1_total_compensation": str(total_comp),
        "line_2_statutory_minimum_wage": str(min_wage),
        "line_3_nontaxable_13th_month": str(thirteenth),
        "line_4_nontaxable_deminimis": str(deminimis),
        "line_5_sss_gsis_phic_hdmf": str(sss_gsis),
        "line_6_other_nontaxable": str(other_nt),
        "line_7_total_nontaxable": str(total_nontaxable),
        "line_8_taxable_compensation": str(taxable_comp),
        "line_9_tax_withheld": str(tax_withheld),
        "line_10_adjustment": str(adjustment),
        "line_11_total_tax_remitted": str(total_tax_remitted),
        "line_12_surcharge": str(surcharge),
        "line_13_interest": str(interest),
        "line_14_compromise": str(compromise),
        "line_15_total_penalties": str(total_penalties),
        "line_16_total_amount_due": str(total_due),
    }


def calculate_bir_0619e(
    ewt_data: dict[str, Any],
) -> dict[str, Any]:
    """Calculate BIR 0619-E (Monthly Remittance of Expanded Withholding Tax).

    Args:
        ewt_data: Dict with keys matching 0619-E fields.
    """
    total_income = Decimal(str(ewt_data.get("total_income_payments", 0)))
    total_withheld = Decimal(str(ewt_data.get("total_taxes_withheld", 0)))
    adjustment = Decimal(str(ewt_data.get("adjustment", 0)))
    surcharge = Decimal(str(ewt_data.get("surcharge", 0)))
    interest = Decimal(str(ewt_data.get("interest", 0)))
    compromise = Decimal(str(ewt_data.get("compromise", 0)))

    tax_still_due = max(total_withheld - adjustment, Decimal("0"))
    total_penalties = surcharge + interest + compromise
    total_due = tax_still_due + total_penalties

    return {
        "line_1_total_amount_of_income_payments": str(total_income),
        "line_2_total_taxes_withheld": str(total_withheld),
        "line_3_adjustment": str(adjustment),
        "line_4_tax_still_due": str(tax_still_due),
        "line_5_surcharge": str(surcharge),
        "line_6_interest": str(interest),
        "line_7_compromise": str(compromise),
        "line_8_total_penalties": str(total_penalties),
        "line_9_total_amount_due": str(total_due),
    }


async def calculate_report(
    form_type: str,
    sales_data: list[dict] | None = None,
    purchases_data: list[dict] | None = None,
    db: Any = None,
    tax_credits: Decimal | str | None = None,
    penalties: Decimal | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Generic entry point: try schema from DB first, fallback to hardcoded.

    Args:
        form_type: BIR form type (e.g. "BIR_2550M").
        sales_data: List of sales records.
        purchases_data: List of purchase records.
        db: Optional AsyncSession — if provided, tries to load schema from DB.
        tax_credits: Optional tax credits.
        penalties: Optional penalties.

    Returns:
        Calculated report data dict.
    """
    # Try schema-based calculation if DB session provided
    if db is not None:
        try:
            from backend.services.schema_registry import evaluate_formulas, get_form_schema

            schema = await get_form_schema(form_type, db)
            if schema:
                # Aggregate raw data into base fields
                base_fields = _aggregate_base_fields(
                    form_type, sales_data or [], purchases_data or [], tax_credits, penalties
                )
                # Evaluate formulas from schema
                return evaluate_formulas(schema, base_fields)
        except Exception:
            pass  # Fall through to hardcoded

    # Fallback to hardcoded calculators
    if form_type == "BIR_2550M":
        return calculate_bir_2550m(sales_data, purchases_data, tax_credits, penalties)
    if form_type == "BIR_2550Q":
        return calculate_bir_2550q(sales_data, purchases_data, tax_credits, penalties)
    if form_type == "BIR_1601C":
        return calculate_bir_1601c(kwargs.get("compensation_data", {}))
    if form_type == "BIR_0619E":
        return calculate_bir_0619e(kwargs.get("ewt_data", {}))

    raise ValueError(f"No calculator available for {form_type}")


def _aggregate_base_fields(
    form_type: str,
    sales_data: list[dict],
    purchases_data: list[dict],
    tax_credits: Decimal | str | None = None,
    penalties: Decimal | str | None = None,
) -> dict[str, str]:
    """Aggregate raw sales/purchase data into base (editable) fields for any VAT form."""
    vatable_sales = Decimal("0")
    sales_to_government = Decimal("0")
    zero_rated_sales = Decimal("0")
    vat_exempt_sales = Decimal("0")

    for row in sales_data:
        amount = Decimal(str(row.get("amount", 0)))
        vat_type = str(row.get("vat_type", "vatable")).lower().strip()
        if vat_type == "government":
            sales_to_government += amount
        elif vat_type == "zero_rated":
            zero_rated_sales += amount
        elif vat_type == "exempt":
            vat_exempt_sales += amount
        else:
            vatable_sales += amount

    input_vat_goods = Decimal("0")
    input_vat_capital = Decimal("0")
    input_vat_services = Decimal("0")
    input_vat_imports = Decimal("0")

    for row in purchases_data:
        amount = Decimal(str(row.get("amount", 0)))
        vat_amount = Decimal(str(row.get("vat_amount", 0)))
        category = str(row.get("category", "goods")).lower().strip()
        input_vat = vat_amount if vat_amount else amount * VAT_RATE
        if category == "capital":
            input_vat_capital += input_vat
        elif category == "services":
            input_vat_services += input_vat
        elif category == "imports":
            input_vat_imports += input_vat
        else:
            input_vat_goods += input_vat

    return {
        "line_1_vatable_sales": str(vatable_sales),
        "line_2_sales_to_government": str(sales_to_government),
        "line_3_zero_rated_sales": str(zero_rated_sales),
        "line_4_exempt_sales": str(vat_exempt_sales),
        "line_7_input_vat_goods": str(input_vat_goods),
        "line_8_input_vat_capital": str(input_vat_capital),
        "line_9_input_vat_services": str(input_vat_services),
        "line_10_input_vat_imports": str(input_vat_imports),
        "line_13_less_tax_credits": str(Decimal(str(tax_credits)) if tax_credits else Decimal("0")),
        "line_15_add_penalties": str(Decimal(str(penalties)) if penalties else Decimal("0")),
    }


def get_supported_forms() -> dict:
    """Return all supported BIR form types with availability status."""
    return {
        k: {
            "name": v["name"],
            "frequency": v["frequency"],
            "status": v.get("status", "active"),
        }
        for k, v in SUPPORTED_FORMS.items()
    }
