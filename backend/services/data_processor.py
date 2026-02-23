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


def extract_full_data(file_content: bytes, filename: str, sheet_name: str = "Sheet1") -> list[dict]:
    """Extract all rows from a specific sheet as a list of dicts."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_name)
    else:
        df = pd.read_csv(io.BytesIO(file_content))
    df = _clean_dataframe(df)
    return df.to_dict(orient="records")
