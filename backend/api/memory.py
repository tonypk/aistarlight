from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.tenant import User
from backend.repositories.memory import CorrectionRepository
from backend.schemas.common import ok
from backend.schemas.memory import PreferenceUpdate
from backend.services.audit_logger import log_action
from backend.services.memory_manager import delete_preference, get_preference, get_preferences, upsert_preference

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/preferences")
async def list_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List all saved preferences for this tenant."""
    prefs = await get_preferences(user.tenant_id, db)
    return ok(prefs)


@router.get("/preferences/{report_type}")
async def get_pref(
    report_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get preference for a specific report type."""
    pref = await get_preference(user.tenant_id, report_type, db)
    if not pref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
    return ok(pref)


@router.put("/preferences/{report_type}")
async def update_pref(
    report_type: str,
    data: PreferenceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Create or update preference for a report type."""
    pref = await upsert_preference(
        tenant_id=user.tenant_id,
        report_type=report_type,
        column_mappings=data.column_mappings,
        format_rules=data.format_rules,
        auto_fill_rules=data.auto_fill_rules,
        db=db,
    )

    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        entity_type="preference",
        entity_id=None,
        action="upsert",
        changes={"report_type": report_type},
    )

    return ok(pref)


@router.delete("/preferences/{report_type}")
async def remove_pref(
    report_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Delete preference for a report type."""
    deleted = await delete_preference(user.tenant_id, report_type, db)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")

    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        entity_type="preference",
        entity_id=None,
        action="delete",
        changes={"report_type": report_type},
    )

    return ok({"deleted": True})


@router.get("/corrections")
async def list_corrections(
    page: int = 1,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List correction history."""
    repo = CorrectionRepository(db)
    offset = (page - 1) * limit
    corrections = await repo.find_by_tenant(user.tenant_id, offset=offset, limit=limit)
    total = await repo.count(tenant_id=user.tenant_id)
    return ok(
        [
            {
                "id": str(c.id),
                "report_type": c.report_type,
                "field_name": c.field_name,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "reason": c.reason,
                "created_at": c.created_at.isoformat(),
            }
            for c in corrections
        ],
        meta={"total": total, "page": page, "limit": limit},
    )
