"""Bank reconciliation API endpoints."""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.deps import get_current_user, get_session
from backend.models.tenant import User
from backend.repositories.bank_recon_repo import BankReconBatchRepository
from backend.schemas.bank_recon import (
    BankReconBatchListItem,
    BankReconBatchResponse,
    SuggestionActionRequest,
)
from backend.schemas.common import ok, fail
from backend.services.bank_reconciliation_service import process_bank_reconciliation

router = APIRouter(prefix="/bank-recon", tags=["bank-recon"])


@router.post("/process")
async def process_reconciliation(
    files: list[UploadFile] = File(...),
    period: str = Form(...),
    session_id: str | None = Form(None),
    amount_tolerance: float = Form(0.01),
    date_tolerance_days: int = Form(3),
    run_ai_analysis: bool = Form(True),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Upload bank/billing files and run auto-reconciliation."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    # Read file contents
    file_pairs: list[tuple[str, bytes]] = []
    for f in files:
        content = await f.read()
        if len(content) > settings.max_upload_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File {f.filename} exceeds {settings.max_upload_size_mb}MB limit",
            )
        file_pairs.append((f.filename or "unknown", content))

    parsed_session_id = None
    if session_id:
        try:
            parsed_session_id = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session_id format")

    batch = await process_bank_reconciliation(
        files=file_pairs,
        tenant_id=user.tenant_id,
        user_id=user.id,
        period=period,
        db=db,
        session_id=parsed_session_id,
        amount_tolerance=amount_tolerance,
        date_tolerance_days=date_tolerance_days,
        run_ai_analysis=run_ai_analysis,
    )

    return ok(BankReconBatchResponse.model_validate(batch).model_dump(mode="json"))


@router.get("/batches")
async def list_batches(
    page: int = 1,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List bank reconciliation batches."""
    repo = BankReconBatchRepository(db)
    offset = (page - 1) * limit
    batches = await repo.find_by_tenant(user.tenant_id, offset=offset, limit=limit)
    total = await repo.count_by_tenant(user.tenant_id)

    items = []
    for b in batches:
        match_rate = None
        if b.match_result and isinstance(b.match_result, dict):
            match_rate = b.match_result.get("match_rate")
        items.append(BankReconBatchListItem(
            id=b.id,
            status=b.status,
            period=b.period,
            total_entries=b.total_entries,
            source_files=b.source_files,
            match_rate=match_rate,
            created_at=b.created_at,
        ).model_dump(mode="json"))

    return ok(items, meta={"total": total, "page": page, "limit": limit})


@router.get("/batches/{batch_id}")
async def get_batch(
    batch_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get bank reconciliation batch detail."""
    repo = BankReconBatchRepository(db)
    batch = await repo.get_by_id(batch_id)
    if not batch or batch.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    return ok(BankReconBatchResponse.model_validate(batch).model_dump(mode="json"))


@router.post("/batches/{batch_id}/accept-suggestion")
async def accept_suggestion(
    batch_id: uuid.UUID,
    body: SuggestionActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Accept an AI match suggestion."""
    repo = BankReconBatchRepository(db)
    batch = await repo.get_by_id(batch_id)
    if not batch or batch.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    suggestions = list(batch.ai_suggestions or [])
    if body.suggestion_index >= len(suggestions):
        raise HTTPException(status_code=400, detail="Invalid suggestion index")

    updated = {**suggestions[body.suggestion_index], "status": "accepted"}
    new_suggestions = [
        updated if i == body.suggestion_index else s
        for i, s in enumerate(suggestions)
    ]

    await repo.update(batch, ai_suggestions=new_suggestions)
    await db.commit()

    return ok({"message": "Suggestion accepted", "suggestion": updated})


@router.post("/batches/{batch_id}/reject-suggestion")
async def reject_suggestion(
    batch_id: uuid.UUID,
    body: SuggestionActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Reject an AI match suggestion."""
    repo = BankReconBatchRepository(db)
    batch = await repo.get_by_id(batch_id)
    if not batch or batch.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    suggestions = list(batch.ai_suggestions or [])
    if body.suggestion_index >= len(suggestions):
        raise HTTPException(status_code=400, detail="Invalid suggestion index")

    updated = {**suggestions[body.suggestion_index], "status": "rejected"}
    new_suggestions = [
        updated if i == body.suggestion_index else s
        for i, s in enumerate(suggestions)
    ]

    await repo.update(batch, ai_suggestions=new_suggestions)
    await db.commit()

    return ok({"message": "Suggestion rejected", "suggestion": updated})


@router.post("/batches/{batch_id}/rerun-analysis")
async def rerun_analysis(
    batch_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Re-run AI analysis on remaining unmatched entries."""
    from backend.services.match_analyzer import analyze_unmatched_entries

    repo = BankReconBatchRepository(db)
    batch = await repo.get_by_id(batch_id)
    if not batch or batch.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status != "completed":
        raise HTTPException(status_code=400, detail="Batch must be completed to rerun analysis")

    match_result = batch.match_result or {}
    unmatched_bank = match_result.get("unmatched_bank", [])
    unmatched_records = match_result.get("unmatched_records", [])

    if not unmatched_bank and not unmatched_records:
        return ok({"message": "No unmatched entries to analyze"})

    await repo.update(batch, status="analyzing")
    await db.flush()

    try:
        suggestions, explanations = await analyze_unmatched_entries(
            unmatched_bank=unmatched_bank,
            unmatched_records=unmatched_records,
            all_records=unmatched_records,
            all_bank=unmatched_bank,
            max_suggestions=settings.max_ai_suggestions,
        )

        from dataclasses import asdict

        await repo.update(
            batch,
            status="completed",
            ai_suggestions=[{**asdict(s), "status": "pending"} for s in suggestions],
            ai_explanations=[asdict(e) for e in explanations],
        )
        await db.commit()

        return ok(BankReconBatchResponse.model_validate(batch).model_dump(mode="json"))

    except Exception as e:
        await repo.update(batch, status="completed", error_message=str(e)[:500])
        await db.commit()
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")
