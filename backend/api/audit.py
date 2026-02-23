import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.tenant import User
from backend.repositories.audit import AuditRepository
from backend.schemas.common import ok

router = APIRouter(prefix="/audit", tags=["audit"])


def _format_log(log):
    return {
        "id": str(log.id),
        "tenant_id": str(log.tenant_id),
        "user_id": str(log.user_id) if log.user_id else None,
        "entity_type": log.entity_type,
        "entity_id": str(log.entity_id) if log.entity_id else None,
        "action": log.action,
        "changes": log.changes,
        "comment": log.comment,
        "created_at": log.created_at.isoformat(),
    }


@router.get("")
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List all audit logs for the current tenant."""
    repo = AuditRepository(db)
    offset = (page - 1) * limit
    logs = await repo.find_by_tenant(user.tenant_id, offset=offset, limit=limit)
    total = await repo.count(tenant_id=user.tenant_id)
    return ok(
        [_format_log(log) for log in logs],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.get("/report/{report_id}")
async def get_report_audit(
    report_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get audit logs for a specific report."""
    repo = AuditRepository(db)
    offset = (page - 1) * limit
    logs = await repo.find_by_report(uuid.UUID(report_id), offset=offset, limit=limit)
    total = await repo.count(entity_type="report", entity_id=uuid.UUID(report_id))
    return ok(
        [_format_log(log) for log in logs],
        meta={"total": total, "page": page, "limit": limit},
    )
