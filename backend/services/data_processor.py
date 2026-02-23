"""Excel/CSV data processor for parsing uploaded financial data."""

import io
from typing import Any

import pandas as pd


def parse_file(file_content: bytes, filename: str) -> dict[str, Any]:
    """Parse uploaded Excel or CSV file and return structured data."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("xlsx", "xls"):
        return _parse_excel(file_content)
    elif ext == "csv":
        return _parse_csv(file_content)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .xlsx, .xls, or .csv")


def _parse_excel(content: bytes) -> dict[str, Any]:
    xls = pd.ExcelFile(io.BytesIO(content))
    sheets = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        df = _clean_dataframe(df)
        sheets[sheet_name] = {
            "columns": list(df.columns),
            "row_count": len(df),
            "preview": df.head(10).to_dict(orient="records"),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }
    return {"type": "excel", "sheets": sheets}


def _parse_csv(content: bytes) -> dict[str, Any]:
    df = pd.read_csv(io.BytesIO(content))
    df = _clean_dataframe(df)
    return {
        "type": "csv",
        "sheets": {
            "Sheet1": {
                "columns": list(df.columns),
                "row_count": len(df),
                "preview": df.head(10).to_dict(orient="records"),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            }
        },
    }


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up a dataframe: strip whitespace, drop empty rows."""
    # Strip whitespace from string columns
    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
    # Drop fully empty rows
    df = df.dropna(how="all")
    # Replace NaN with None for JSON serialization
    df = df.where(pd.notnull(df), None)
    return df


def extract_full_data(file_content: bytes, filename: str, sheet_name: str | None = None) -> list[dict]:
    """Extract all rows from a specific sheet as a list of dicts.

    If sheet_name is None, reads the first sheet for Excel files.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("xlsx", "xls"):
        if sheet_name:
            df = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_name)
        else:
            # Read the first sheet (index 0)
            df = pd.read_excel(io.BytesIO(file_content), sheet_name=0)
    else:
        df = pd.read_csv(io.BytesIO(file_content))
    df = _clean_dataframe(df)
    return df.to_dict(orient="records")


def apply_column_mapping(
    rows: list[dict],
    column_mappings: dict[str, str],
) -> tuple[list[dict], list[dict]]:
    """Apply column mappings to raw data rows, separating into sales and purchases.

    column_mappings: {source_column: target_field}
    target fields: date, description, amount, vat_amount, vat_type, category, tin, _skip

    Returns (sales_data, purchases_data).
    Sales: rows where category is not in ('goods', 'services', 'capital') or no category.
    Purchases: rows where category is in ('goods', 'services', 'capital').
    """
    # Build reverse mapping: target_field -> source_column
    reverse_map = {target: source for source, target in column_mappings.items() if target != "_skip"}

    mapped_rows = []
    for row in rows:
        mapped = {}
        for target_field, source_col in reverse_map.items():
            mapped[target_field] = row.get(source_col)
        mapped_rows.append(mapped)

    sales_data = []
    purchases_data = []
    purchase_categories = {"goods", "services", "capital"}

    for row in mapped_rows:
        category = str(row.get("category", "")).lower().strip()
        amount_raw = row.get("amount")
        try:
            amount = float(str(amount_raw)) if amount_raw is not None else 0.0
        except (ValueError, TypeError):
            amount = 0.0

        vat_amount_raw = row.get("vat_amount")
        try:
            vat_amount = float(str(vat_amount_raw)) if vat_amount_raw is not None else 0.0
        except (ValueError, TypeError):
            vat_amount = 0.0

        entry = {
            "date": row.get("date"),
            "description": row.get("description"),
            "amount": amount,
            "vat_amount": vat_amount,
            "vat_type": row.get("vat_type", "vatable"),
            "category": category if category in purchase_categories else "goods",
            "tin": row.get("tin"),
        }

        if category in purchase_categories:
            purchases_data.append(entry)
        else:
            sales_data.append(entry)

    return sales_data, purchases_data
