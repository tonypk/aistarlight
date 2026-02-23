"""Seed BIR 2550M form schema into the database.

Usage:
    python scripts/seed_form_schemas.py

Or in Docker:
    docker compose exec backend python scripts/seed_form_schemas.py
"""

import asyncio
import uuid

from sqlalchemy import select

from backend.core.database import engine
from backend.models.form_schema import FormSchema

BIR_2550M_SCHEMA_DEF = {
    "sections": [
        {
            "id": "part2_sales",
            "name": "Part II - Sales / Receipts",
            "fields": [
                {
                    "id": "line_1_vatable_sales",
                    "line": "1",
                    "label": "Vatable Sales / Receipts",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_2_sales_to_government",
                    "line": "2",
                    "label": "Sales to Government (subject to 5% Final Withholding VAT)",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_3_zero_rated_sales",
                    "line": "3",
                    "label": "Zero-Rated Sales",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_4_exempt_sales",
                    "line": "4",
                    "label": "Exempt Sales",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_5_total_sales",
                    "line": "5",
                    "label": "Total Sales / Receipts (Sum of Lines 1 to 4)",
                    "editable": False,
                },
            ],
        },
        {
            "id": "part3_output_tax",
            "name": "Part III - Output Tax",
            "fields": [
                {
                    "id": "line_6_output_vat",
                    "line": "6",
                    "label": "Output VAT (Line 1 x 12%)",
                    "editable": False,
                },
                {
                    "id": "line_6a_output_vat_government",
                    "line": "6A",
                    "label": "Output VAT on Sales to Government (Line 2 x 5%)",
                    "editable": False,
                },
                {
                    "id": "line_6b_total_output_vat",
                    "line": "6B",
                    "label": "Total Output Tax (Line 6 + Line 6A)",
                    "editable": False,
                },
            ],
        },
        {
            "id": "part4_input_tax",
            "name": "Part IV - Allowable Input Tax",
            "fields": [
                {
                    "id": "line_7_input_vat_goods",
                    "line": "7",
                    "label": "Input VAT on Domestic Purchases of Goods",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_8_input_vat_capital",
                    "line": "8",
                    "label": "Input VAT on Domestic Purchases of Capital Goods",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_9_input_vat_services",
                    "line": "9",
                    "label": "Input VAT on Domestic Purchases of Services",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_10_input_vat_imports",
                    "line": "10",
                    "label": "Input VAT on Importation of Goods",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_11_total_input_vat",
                    "line": "11",
                    "label": "Total Input Tax (Sum of Lines 7 to 10)",
                    "editable": False,
                },
            ],
        },
        {
            "id": "part5_tax_due",
            "name": "Part V - Tax Due",
            "fields": [
                {
                    "id": "line_12_vat_payable",
                    "line": "12",
                    "label": "VAT Payable (Line 6B - Line 11)",
                    "editable": False,
                },
                {
                    "id": "line_13_less_tax_credits",
                    "line": "13",
                    "label": "Less: Tax Credits / Payments",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_14_net_vat_payable",
                    "line": "14",
                    "label": "Net VAT Payable (Line 12 - Line 13)",
                    "editable": False,
                },
                {
                    "id": "line_15_add_penalties",
                    "line": "15",
                    "label": "Add: Penalties (Surcharge, Interest, Compromise)",
                    "editable": True,
                    "required": False,
                },
                {
                    "id": "line_16_total_amount_due",
                    "line": "16",
                    "label": "TOTAL AMOUNT DUE (Line 14 + Line 15)",
                    "editable": False,
                },
            ],
        },
    ],
}

# Calculation rules — evaluated in order (topologically sorted)
# Each rule is: field_id → formula expression
BIR_2550M_CALCULATION_RULES = {
    "line_5_total_sales": "line_1_vatable_sales + line_2_sales_to_government + line_3_zero_rated_sales + line_4_exempt_sales",
    "line_6_output_vat": "line_1_vatable_sales * 0.12",
    "line_6a_output_vat_government": "line_2_sales_to_government * 0.05",
    "line_6b_total_output_vat": "line_6_output_vat + line_6a_output_vat_government",
    "line_11_total_input_vat": "line_7_input_vat_goods + line_8_input_vat_capital + line_9_input_vat_services + line_10_input_vat_imports",
    "line_12_vat_payable": "line_6b_total_output_vat - line_11_total_input_vat",
    "line_14_net_vat_payable": "max(line_12_vat_payable - line_13_less_tax_credits, 0)",
    "tax_credit_carried_forward": "max(-(line_12_vat_payable - line_13_less_tax_credits), 0)",
    "line_16_total_amount_due": "line_14_net_vat_payable + line_15_add_penalties",
}

# ---------- BIR 2550Q (Quarterly VAT Return) ----------
# Same structure as 2550M with quarterly period label
BIR_2550Q_SCHEMA_DEF = {
    "sections": [
        {
            "id": "part2_sales",
            "name": "Part II - Sales / Receipts (Quarterly)",
            "fields": [
                {"id": "line_1_vatable_sales", "line": "14A", "label": "Vatable Sales / Receipts", "editable": True, "required": False},
                {"id": "line_2_sales_to_government", "line": "14B", "label": "Sales to Government (5% Final Withholding VAT)", "editable": True, "required": False},
                {"id": "line_3_zero_rated_sales", "line": "14C", "label": "Zero-Rated Sales", "editable": True, "required": False},
                {"id": "line_4_exempt_sales", "line": "14D", "label": "Exempt Sales", "editable": True, "required": False},
                {"id": "line_5_total_sales", "line": "15", "label": "Total Sales / Receipts (Sum of Lines 14A to 14D)", "editable": False},
            ],
        },
        {
            "id": "part3_output_tax",
            "name": "Part III - Output Tax",
            "fields": [
                {"id": "line_6_output_vat", "line": "16", "label": "Output VAT (Line 14A x 12%)", "editable": False},
                {"id": "line_6a_output_vat_government", "line": "16A", "label": "Output VAT on Government Sales (Line 14B x 5%)", "editable": False},
                {"id": "line_6b_total_output_vat", "line": "16B", "label": "Total Output Tax (Line 16 + Line 16A)", "editable": False},
            ],
        },
        {
            "id": "part4_input_tax",
            "name": "Part IV - Allowable Input Tax",
            "fields": [
                {"id": "line_7_input_vat_goods", "line": "17", "label": "Input VAT on Domestic Purchases of Goods", "editable": True, "required": False},
                {"id": "line_8_input_vat_capital", "line": "18", "label": "Input VAT on Domestic Purchases of Capital Goods", "editable": True, "required": False},
                {"id": "line_9_input_vat_services", "line": "19", "label": "Input VAT on Domestic Purchases of Services", "editable": True, "required": False},
                {"id": "line_10_input_vat_imports", "line": "20", "label": "Input VAT on Importation of Goods", "editable": True, "required": False},
                {"id": "line_11_total_input_vat", "line": "21", "label": "Total Input Tax (Sum of Lines 17 to 20)", "editable": False},
            ],
        },
        {
            "id": "part5_tax_due",
            "name": "Part V - Tax Due",
            "fields": [
                {"id": "line_12_vat_payable", "line": "22", "label": "VAT Payable (Line 16B - Line 21)", "editable": False},
                {"id": "line_13_less_tax_credits", "line": "23", "label": "Less: Tax Credits / Payments", "editable": True, "required": False},
                {"id": "line_14_net_vat_payable", "line": "24", "label": "Net VAT Payable (Line 22 - Line 23)", "editable": False},
                {"id": "line_15_add_penalties", "line": "25", "label": "Add: Penalties (Surcharge, Interest, Compromise)", "editable": True, "required": False},
                {"id": "line_16_total_amount_due", "line": "26", "label": "TOTAL AMOUNT DUE (Line 24 + Line 25)", "editable": False},
            ],
        },
    ],
}

BIR_2550Q_CALCULATION_RULES = BIR_2550M_CALCULATION_RULES  # Same formulas

# ---------- BIR 1601-C (Monthly Withholding Tax on Compensation) ----------
BIR_1601C_SCHEMA_DEF = {
    "sections": [
        {
            "id": "part1_background",
            "name": "Part I - Background Information",
            "fields": [
                {"id": "tin", "line": "", "label": "TIN", "editable": False},
                {"id": "rdo_code", "line": "", "label": "RDO Code", "editable": False},
                {"id": "company_name", "line": "", "label": "Registered Name", "editable": False},
                {"id": "period", "line": "", "label": "Taxable Month", "editable": False},
            ],
        },
        {
            "id": "part2_computation",
            "name": "Part II - Computation of Tax",
            "fields": [
                {"id": "line_1_total_compensation", "line": "1", "label": "Total Amount of Compensation Paid", "editable": True, "required": True},
                {"id": "line_2_statutory_minimum_wage", "line": "2", "label": "Less: Statutory Minimum Wage / Holiday / Overtime / Night Differential", "editable": True, "required": False},
                {"id": "line_3_nontaxable_13th_month", "line": "3", "label": "Less: Non-Taxable 13th Month Pay & Other Benefits (up to PHP 90,000)", "editable": True, "required": False},
                {"id": "line_4_nontaxable_deminimis", "line": "4", "label": "Less: De Minimis Benefits", "editable": True, "required": False},
                {"id": "line_5_sss_gsis_phic_hdmf", "line": "5", "label": "Less: SSS/GSIS/PHIC/HDMF Mandatory Contributions", "editable": True, "required": False},
                {"id": "line_6_other_nontaxable", "line": "6", "label": "Less: Other Non-Taxable Compensation", "editable": True, "required": False},
                {"id": "line_7_total_nontaxable", "line": "7", "label": "Total Non-Taxable Compensation (Lines 2 to 6)", "editable": False},
                {"id": "line_8_taxable_compensation", "line": "8", "label": "Taxable Compensation (Line 1 - Line 7)", "editable": False},
                {"id": "line_9_tax_withheld", "line": "9", "label": "Tax Required to be Withheld (per Withholding Tax Table)", "editable": True, "required": True},
                {"id": "line_10_adjustment", "line": "10", "label": "Adjustment for Over/Under Withholding from Previous Month(s)", "editable": True, "required": False},
                {"id": "line_11_total_tax_remitted", "line": "11", "label": "Total Tax to be Remitted (Line 9 + Line 10)", "editable": False},
            ],
        },
        {
            "id": "part3_penalties",
            "name": "Part III - Penalties",
            "fields": [
                {"id": "line_12_surcharge", "line": "12", "label": "Surcharge", "editable": True, "required": False},
                {"id": "line_13_interest", "line": "13", "label": "Interest", "editable": True, "required": False},
                {"id": "line_14_compromise", "line": "14", "label": "Compromise Penalty", "editable": True, "required": False},
                {"id": "line_15_total_penalties", "line": "15", "label": "Total Penalties (Lines 12 to 14)", "editable": False},
                {"id": "line_16_total_amount_due", "line": "16", "label": "TOTAL AMOUNT DUE (Line 11 + Line 15)", "editable": False},
            ],
        },
    ],
}

BIR_1601C_CALCULATION_RULES = {
    "line_7_total_nontaxable": "line_2_statutory_minimum_wage + line_3_nontaxable_13th_month + line_4_nontaxable_deminimis + line_5_sss_gsis_phic_hdmf + line_6_other_nontaxable",
    "line_8_taxable_compensation": "max(line_1_total_compensation - line_7_total_nontaxable, 0)",
    "line_11_total_tax_remitted": "line_9_tax_withheld + line_10_adjustment",
    "line_15_total_penalties": "line_12_surcharge + line_13_interest + line_14_compromise",
    "line_16_total_amount_due": "line_11_total_tax_remitted + line_15_total_penalties",
}

# ---------- BIR 0619-E (Monthly EWT Remittance) ----------
BIR_0619E_SCHEMA_DEF = {
    "sections": [
        {
            "id": "part1_background",
            "name": "Part I - Background Information",
            "fields": [
                {"id": "tin", "line": "", "label": "TIN", "editable": False},
                {"id": "rdo_code", "line": "", "label": "RDO Code", "editable": False},
                {"id": "company_name", "line": "", "label": "Registered Name", "editable": False},
                {"id": "period", "line": "", "label": "For the Month", "editable": False},
            ],
        },
        {
            "id": "part2_computation",
            "name": "Part II - Computation of Tax",
            "fields": [
                {"id": "line_1_total_amount_of_income_payments", "line": "1", "label": "Total Amount of Income Payments", "editable": True, "required": True},
                {"id": "line_2_total_taxes_withheld", "line": "2", "label": "Total Taxes Withheld for the Month", "editable": True, "required": True},
                {"id": "line_3_adjustment", "line": "3", "label": "Adjustment for Over-Remittance from Previous Month(s)", "editable": True, "required": False},
                {"id": "line_4_tax_still_due", "line": "4", "label": "Tax Still Due (Line 2 - Line 3)", "editable": False},
            ],
        },
        {
            "id": "part3_penalties",
            "name": "Part III - Penalties",
            "fields": [
                {"id": "line_5_surcharge", "line": "5", "label": "Surcharge", "editable": True, "required": False},
                {"id": "line_6_interest", "line": "6", "label": "Interest", "editable": True, "required": False},
                {"id": "line_7_compromise", "line": "7", "label": "Compromise Penalty", "editable": True, "required": False},
                {"id": "line_8_total_penalties", "line": "8", "label": "Total Penalties (Lines 5 to 7)", "editable": False},
                {"id": "line_9_total_amount_due", "line": "9", "label": "TOTAL AMOUNT DUE (Line 4 + Line 8)", "editable": False},
            ],
        },
    ],
}

BIR_0619E_CALCULATION_RULES = {
    "line_4_tax_still_due": "max(line_2_total_taxes_withheld - line_3_adjustment, 0)",
    "line_8_total_penalties": "line_5_surcharge + line_6_interest + line_7_compromise",
    "line_9_total_amount_due": "line_4_tax_still_due + line_8_total_penalties",
}

# All form schemas to seed
ALL_SCHEMAS = [
    {
        "form_type": "BIR_2550M",
        "name": "Monthly Value-Added Tax Declaration",
        "frequency": "monthly",
        "schema_def": BIR_2550M_SCHEMA_DEF,
        "calculation_rules": BIR_2550M_CALCULATION_RULES,
    },
    {
        "form_type": "BIR_2550Q",
        "name": "Quarterly Value-Added Tax Return",
        "frequency": "quarterly",
        "schema_def": BIR_2550Q_SCHEMA_DEF,
        "calculation_rules": BIR_2550Q_CALCULATION_RULES,
    },
    {
        "form_type": "BIR_1601C",
        "name": "Monthly Remittance Return of Income Taxes Withheld on Compensation",
        "frequency": "monthly",
        "schema_def": BIR_1601C_SCHEMA_DEF,
        "calculation_rules": BIR_1601C_CALCULATION_RULES,
    },
    {
        "form_type": "BIR_0619E",
        "name": "Monthly Remittance Form for Creditable Income Taxes Withheld (Expanded)",
        "frequency": "monthly",
        "schema_def": BIR_0619E_SCHEMA_DEF,
        "calculation_rules": BIR_0619E_CALCULATION_RULES,
    },
]


async def seed():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        for form in ALL_SCHEMAS:
            existing = await session.execute(
                select(FormSchema).where(FormSchema.form_type == form["form_type"])
            )
            if existing.scalar_one_or_none():
                print(f"{form['form_type']} schema already exists, skipping.")
                continue

            schema = FormSchema(
                id=uuid.uuid4(),
                form_type=form["form_type"],
                version=1,
                name=form["name"],
                frequency=form["frequency"],
                is_active=True,
                schema_def=form["schema_def"],
                calculation_rules=form["calculation_rules"],
            )
            session.add(schema)
            print(f"Seeded {form['form_type']} form schema.")

        await session.commit()
        print("Done! All form schemas seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
