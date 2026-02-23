"""API endpoints for correction tracking and learning."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_tenant, get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.repositories.correction_rule_repo import CorrectionRuleRepository
from backend.schemas.common import ok
from backend.schemas.correction import CorrectionCreate
from backend.services.correction_analyzer import (
    analyze_corrections,
    get_learning_stats,
    persist_candidate_rules,
)
from backend.services.correction_service import (
    get_correction_history,
    get_correction_stats,
    get_entity_corrections,
    record_correction,
)

router = APIRouter(prefix="/corrections", tags=["corrections"])


@router.post("")
async def create_correction(
    data: CorrectionCreate,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Record an accountant's correction."""
    correction = await record_correction(
        db,
        tenant_id=tenant.id,
        user_id=user.id,
        entity_type=data.entity_type,
        entity_id=uuid.UUID(data.entity_id),
        field_name=data.field_name,
        old_value=data.old_value,
        new_value=data.new_value,
        reason=data.reason,
    )
    return ok({
        "id": str(correction.id),
        "entity_type": correction.entity_type,
        "entity_id": str(correction.entity_id),
        "field_name": correction.field_name,
        "old_value": correction.old_value,
        "new_value": correction.new_value,
        "context_data": correction.context_data,
        "created_at": correction.created_at.isoformat(),
    })


@router.get("")
async def list_corrections(
    entity_type: str | None = Query(None),
    field_name: str | None = Query(None),
    since: str | None = Query(None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """List corrections with filters."""
    since_dt = datetime.fromisoformat(since) if since else None
    items, total = await get_correction_history(
        db,
        tenant_id=tenant.id,
        entity_type=entity_type,
        field_name=field_name,
        since=since_dt,
        page=page,
        limit=limit,
    )
    return ok(items, meta={"total": total, "page": page, "limit": limit})


@router.get("/stats")
async def correction_stats(
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Get correction statistics."""
    stats = await get_correction_stats(db, tenant.id)
    return ok(stats)


@router.get("/entity/{entity_type}/{entity_id}")
async def entity_corrections(
    entity_type: str,
    entity_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get correction history for a specific entity."""
    corrections = await get_entity_corrections(
        db, entity_type, uuid.UUID(entity_id)
    )
    return ok(corrections)


# --- Learning endpoints ---


@router.get("/learning/stats")
async def learning_stats(
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Get learning system statistics."""
    stats = await get_learning_stats(db, tenant.id)
    return ok(stats)


@router.post("/learning/analyze")
async def trigger_analysis(
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Trigger pattern analysis and generate candidate rules."""
    candidates = await analyze_corrections(db, tenant.id)
    if candidates:
        persisted = await persist_candidate_rules(db, tenant.id, candidates)
        return ok(persisted)
    return ok([])


@router.get("/rules")
async def list_rules(
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """List learned correction rules."""
    repo = CorrectionRuleRepository(db)
    rules = await repo.find_by_tenant(tenant.id)
    return ok([
        {
            "id": str(r.id),
            "rule_type": r.rule_type,
            "match_criteria": r.match_criteria,
            "correction_field": r.correction_field,
            "correction_value": r.correction_value,
            "confidence": float(r.confidence),
            "source_correction_count": r.source_correction_count,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat(),
        }
        for r in rules
    ])


@router.patch("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    data: dict,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Activate or deactivate a learned rule."""
    repo = CorrectionRuleRepository(db)
    rule = await repo.get_by_id(uuid.UUID(rule_id))
    if not rule or rule.tenant_id != tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if "is_active" in data:
        if data["is_active"]:
            rule = await repo.activate(rule.id)
        else:
            rule = await repo.deactivate(rule.id)

    return ok({
        "id": str(rule.id),
        "is_active": rule.is_active,
    })
