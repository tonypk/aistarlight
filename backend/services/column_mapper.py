"""AI-powered column mapping: maps user's spreadsheet columns to BIR form fields."""

import json

from backend.core.llm import chat_completion

MAPPING_SYSTEM_PROMPT = """You are an expert Philippine tax accountant assistant.
Your task is to map spreadsheet column names to standard BIR form fields.

For BIR 2550M (Monthly VAT), the target fields are:
- date: Transaction date
- description: Item/transaction description
- amount: Transaction amount (net of VAT)
- vat_amount: VAT amount
- vat_type: One of "vatable", "exempt", "zero_rated"
- category: One of "goods", "services", "capital" (for purchases)
- tin: TIN of supplier/customer

Respond ONLY with valid JSON in this format:
{
  "mappings": {
    "source_column_name": "target_field_name",
    ...
  },
  "unmapped": ["column_names_that_dont_map"],
  "confidence": 0.95
}
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
