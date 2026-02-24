"""Excel/CSV data processor for parsing uploaded financial data."""

import io
from typing import Any

import pandas as pd


# Minimum ratio of non-empty cells in a row to consider it a header row.
_HEADER_MIN_FILL_RATIO = 0.4
# Maximum number of rows to scan when looking for the header row.
_HEADER_SCAN_LIMIT = 20


def parse_file(file_content: bytes, filename: str) -> dict[str, Any]:
    """Parse uploaded Excel or CSV file and return structured data."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("xlsx", "xls"):
        return _parse_excel(file_content)
    elif ext == "csv":
        return _parse_csv(file_content)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .xlsx, .xls, or .csv")


def _detect_header_row(raw_df: pd.DataFrame) -> int:
    """Auto-detect the real header row in a DataFrame read with header=None.

    BIR forms and similar documents have merged title cells at the top
    (e.g. "PURCHASE TRANSACTION"), metadata rows ("TIN:", "PERIOD:"),
    and then the actual column headers further down.

    Strategy: scan the first N rows and pick the one with the highest
    ratio of non-empty, unique, string-like cells — that's the header.
    """
    best_row = 0
    best_score = 0.0
    total_cols = len(raw_df.columns)

    scan_limit = min(_HEADER_SCAN_LIMIT, len(raw_df))
    for i in range(scan_limit):
        row = raw_df.iloc[i]
        non_empty = 0
        values = set()
        for v in row:
            s = str(v).strip() if pd.notna(v) else ""
            if s and s.lower() != "nan":
                non_empty += 1
                values.add(s)

        if total_cols == 0:
            continue

        fill_ratio = non_empty / total_cols
        # Prefer rows where most cells are non-empty AND unique (real headers
        # are distinct; merged title rows have one value repeated or mostly empty).
        uniqueness = len(values) / max(non_empty, 1)
        score = fill_ratio * uniqueness

        # Require minimum fill to even consider the row.
        if fill_ratio >= _HEADER_MIN_FILL_RATIO and score > best_score:
            best_score = score
            best_row = i

    return best_row


def _read_excel_sheet(xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    """Read a single Excel sheet with smart header detection."""
    # First pass: read without headers to inspect raw data.
    raw_df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

    if raw_df.empty:
        return raw_df

    header_row = _detect_header_row(raw_df)

    # Second pass: re-read with the detected header row.
    df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)

    # Clean up any remaining "Unnamed: X" columns (from merged cells even in
    # the detected header row) by replacing them with empty strings.
    renamed = {}
    for col in df.columns:
        col_str = str(col)
        if col_str.startswith("Unnamed:"):
            renamed[col] = ""
    if renamed:
        df = df.rename(columns=renamed)

    # Drop columns that are entirely empty (no header and no data).
    df = df.loc[:, ~((df.columns == "") & df.isna().all())]

    return df


def _parse_excel(content: bytes) -> dict[str, Any]:
    xls = pd.ExcelFile(io.BytesIO(content))
    sheets = {}
    for sheet_name in xls.sheet_names:
        df = _read_excel_sheet(xls, sheet_name)
        df = _clean_dataframe(df)
        sheets[sheet_name] = {
            "columns": [str(c) for c in df.columns],
            "row_count": len(df),
            "preview": df.head(10).to_dict(orient="records"),
            "dtypes": {str(col): str(dtype) for col, dtype in df.dtypes.items()},
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
        xls = pd.ExcelFile(io.BytesIO(file_content))
        target = sheet_name if sheet_name else xls.sheet_names[0]
        df = _read_excel_sheet(xls, target)
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

    vat_type: vatable, exempt, zero_rated, government
    category (purchases): goods, services, capital, imports

    Returns (sales_data, purchases_data).
    Sales: rows where category is not in purchase_categories or no category.
    Purchases: rows where category is in purchase_categories.
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
    purchase_categories = {"goods", "services", "capital", "imports"}

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
            "category": category if category in purchase_categories else ("imports" if category == "imports" else "goods"),
            "tin": row.get("tin"),
        }

        if category in purchase_categories:
            purchases_data.append(entry)
        else:
            sales_data.append(entry)

    return sales_data, purchases_data
