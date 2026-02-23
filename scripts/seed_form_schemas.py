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


async def seed():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Check if already seeded
        existing = await session.execute(
            select(FormSchema).where(FormSchema.form_type == "BIR_2550M")
        )
        if existing.scalar_one_or_none():
            print("BIR_2550M schema already exists, skipping seed.")
            return

        schema = FormSchema(
            id=uuid.uuid4(),
            form_type="BIR_2550M",
            version=1,
            name="Monthly Value-Added Tax Declaration",
            frequency="monthly",
            is_active=True,
            schema_def=BIR_2550M_SCHEMA_DEF,
            calculation_rules=BIR_2550M_CALCULATION_RULES,
        )
        session.add(schema)
        await session.commit()
        print("Seeded BIR_2550M form schema successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
