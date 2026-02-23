"""API endpoints for compliance validation."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_tenant, get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.schemas.common import ok
from backend.services.compliance_service import (
    get_latest_validation,
    get_validation_history,
    validate_report,
)

router = APIRouter(prefix="/reports", tags=["compliance"])


@router.post("/{report_id}/validate")
async def run_validation(
    report_id: str,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Run compliance validation on a report."""
    try:
        result = await validate_report(
            db,
            report_id=uuid.UUID(report_id),
            tenant_id=tenant.id,
            user_id=user.id,
        )
        return ok(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{report_id}/validation")
async def get_validation(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get the latest validation result for a report."""
    result = await get_latest_validation(db, uuid.UUID(report_id))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No validation found. Run POST /validate first.",
        )
    return ok(result)


@router.get("/{report_id}/validation/history")
async def validation_history(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get validation history for a report."""
    results = await get_validation_history(db, uuid.UUID(report_id))
    return ok(results)
