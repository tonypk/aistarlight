import logging
import os
import uuid

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.deps import get_current_user, get_session
from backend.models.tenant import User
from backend.schemas.common import ok
from backend.services.column_mapper import auto_map_columns
from backend.services.data_processor import parse_file
from backend.services.memory_manager import get_preference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload an Excel or CSV file. Returns file_id, columns, and sample rows."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xls", "csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xlsx, .xls, .csv supported")

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    # Parse first to validate before saving
    try:
        parsed = parse_file(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Save to disk only after successful parse
    file_id = str(uuid.uuid4())
    filepath = os.path.join(settings.upload_dir, f"{file_id}.{ext}")
    with open(filepath, "wb") as f:
        f.write(content)

    # Extract columns and sample rows from first sheet
    sheets = parsed.get("sheets", {})
    first_sheet = next(iter(sheets.values()), None)
    columns = first_sheet["columns"] if first_sheet else []
    sample_rows = first_sheet["preview"][:5] if first_sheet else []

    # DEBUG: log detected columns for troubleshooting
    logger.warning("UPLOAD DEBUG: file=%s columns=%s", file.filename, columns)

    return ok({
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "columns": columns,
        "sample_rows": sample_rows,
        "sheets": sheets,
    })


@router.post("/preview")
async def preview_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Parse and preview uploaded file structure."""
    content = await file.read()
    try:
        parsed = parse_file(content, file.filename or "file.csv")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ok(parsed)


@router.post("/mapping")
async def suggest_mapping(
    columns: list[str] = Body(...),
    sample_rows: list[dict] = Body(...),
    report_type: str = Body("BIR_2550M"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """AI-powered column mapping suggestion."""
    existing_pref = await get_preference(user.tenant_id, report_type, db)
    existing_mappings = existing_pref["column_mappings"] if existing_pref else None

    mapping_result = await auto_map_columns(
        columns=columns,
        sample_rows=sample_rows,
        report_type=report_type,
        existing_mappings=existing_mappings,
    )
    return ok(mapping_result)
