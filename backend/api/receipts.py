"""Receipt OCR API endpoints."""

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.tenant import User
from backend.repositories.receipt_repo import ReceiptBatchRepository
from backend.schemas.common import ok
from backend.services.audit_logger import log_action
from backend.services.receipt_service import process_receipt_batch

router = APIRouter(prefix="/receipts", tags=["receipts"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
MAX_BATCH_SIZE = 50


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_receipts(
    files: list[UploadFile] = File(...),
    period: str = Form(...),
    report_type: str = Form(default="BIR_2550M"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Upload receipt images for OCR processing.

    Accepts multiple image files. The system will:
    1. OCR each image using PaddleOCR
    2. Extract fields using rules (TIN, date, amounts, VAT)
    3. Use GPT-4.1 mini for ambiguous fields only
    4. Create transactions and generate a BIR report
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum is {MAX_BATCH_SIZE}.",
        )

    # Validate file types
    images: list[tuple[str, bytes]] = []
    for f in files:
        ext = Path(f.filename or "unknown.jpg").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {f.filename}. Allowed: JPG, PNG, BMP, TIFF, WEBP",
            )
        content = await f.read()
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {f.filename}. Maximum is 20MB per image.",
            )
        images.append((f.filename or "receipt.jpg", content))

    # Validate period format
    if not re.match(r"^\d{4}-\d{2}$", period):
        raise HTTPException(status_code=400, detail="Period must be YYYY-MM format")

    batch = await process_receipt_batch(
        images=images,
        tenant_id=user.tenant_id,
        user_id=user.id,
        period=period,
        report_type=report_type,
        db=db,
    )

    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        entity_type="receipt_batch",
        entity_id=batch.id,
        action="upload",
        changes={
            "total_images": len(images),
            "period": period,
            "report_type": report_type,
        },
    )

    return ok(_batch_response(batch))


@router.get("/batches")
async def list_batches(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List receipt processing batches."""
    repo = ReceiptBatchRepository(db)
    offset = (page - 1) * limit
    batches = await repo.find_by_tenant(user.tenant_id, offset=offset, limit=limit)
    total = await repo.count(tenant_id=user.tenant_id)

    return ok(
        [_batch_response(b) for b in batches],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.get("/batches/{batch_id}")
async def get_batch(
    batch_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get receipt batch details."""
    repo = ReceiptBatchRepository(db)
    try:
        bid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch ID format")
    batch = await repo.get_by_id(bid)
    if not batch or batch.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    return ok(_batch_response(batch))


def _batch_response(batch) -> dict:
    return {
        "id": str(batch.id),
        "status": batch.status,
        "total_images": batch.total_images,
        "processed_count": batch.processed_count,
        "session_id": str(batch.session_id) if batch.session_id else None,
        "report_id": str(batch.report_id) if batch.report_id else None,
        "report_type": batch.report_type,
        "period": batch.period,
        "results": batch.results,
        "error_message": batch.error_message,
        "created_at": batch.created_at.isoformat(),
        "updated_at": batch.updated_at.isoformat(),
    }
