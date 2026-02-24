"""AI-powered column mapping: maps user's spreadsheet columns to BIR form fields."""

import json

from backend.core.llm import chat_completion

MAPPING_SYSTEM_PROMPT = """You are an expert Philippine tax accountant assistant.
Your task is to map spreadsheet column names to standard BIR form fields.

Target fields by form type:

For BIR_2550M / BIR_2550Q (Monthly/Quarterly VAT):
- date: Transaction date
- description: Item/transaction description
- amount: Transaction amount (net of VAT)
- vat_amount: VAT amount
- vat_type: One of "vatable", "exempt", "zero_rated", "government"
- category: One of "goods", "services", "capital", "imports" (for purchases)
- tin: TIN of supplier/customer

For BIR_1601C (Monthly Withholding Tax on Compensation):
- employee_name: Employee name
- tin: Employee TIN
- total_compensation: Gross compensation
- statutory_minimum_wage: Minimum wage amount
- nontaxable_13th_month: 13th month pay (non-taxable portion)
- nontaxable_deminimis: De minimis benefits
- sss_gsis_phic_hdmf: SSS/GSIS/PhilHealth/Pag-IBIG contributions
- other_nontaxable: Other non-taxable income
- tax_withheld: Tax withheld amount

For BIR_0619E (Monthly Expanded Withholding Tax):
- payee_name: Payee name
- tin: Payee TIN
- atc_code: Alphanumeric Tax Code
- income_payment: Income payment amount
- tax_withheld: Tax withheld amount

For bank statements / billing:
- date: Transaction date
- description: Transaction description/narration
- amount: Transaction amount (or debit/credit)
- debit: Debit amount
- credit: Credit amount
- reference: Reference/check number
- balance: Running balance

Respond ONLY with valid JSON in this format:
{
  "mappings": {
    "source_column_name": "target_field_name",
    ...
  },
  "unmapped": ["column_names_that_dont_map"],
  "confidence": 0.95,
  "field_confidence": {"source_column_name": 0.95, ...}
}

field_confidence: per-column confidence (0.0-1.0) indicating how sure you are about each mapping.
"""


async def auto_map_columns(
    columns: list[str],
    sample_rows: list[dict],
    report_type: str = "BIR_2550M",
    existing_mappings: dict | None = None,
) -> dict:
    """Use Claude to automatically map spreadsheet columns to BIR fields."""
    context_parts = [
        f"Report type: {report_type}",
        f"Columns: {columns}",
        f"Sample data (first 3 rows): {json.dumps(sample_rows[:3], default=str)}",
    ]
    if existing_mappings:
        context_parts.append(
            f"Previous mappings from this user (prefer these if columns match): {json.dumps(existing_mappings)}"
        )

    response = await chat_completion(
        messages=[{"role": "user", "content": "\n".join(context_parts)}],
        system=MAPPING_SYSTEM_PROMPT,
        temperature=0.1,
    )

    try:
        # Extract JSON from response
        start = response.index("{")
        end = response.rindex("}") + 1
        return json.loads(response[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"mappings": {}, "unmapped": columns, "confidence": 0.0}
