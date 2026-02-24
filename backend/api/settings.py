from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_tenant, get_current_user, get_session, require_role
from backend.models.tenant import Tenant, User
from backend.repositories.tenant import TenantRepository
from backend.schemas.common import ok
from backend.schemas.tenant import CompanySettingsUpdate
from backend.services.audit_logger import log_action

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/company")
async def get_company(
    tenant: Tenant = Depends(get_current_tenant),
):
    """Get company settings."""
    return ok({
        "id": str(tenant.id),
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
        "vat_classification": tenant.vat_classification,
        "plan": tenant.plan,
    })


@router.get("/team")
async def list_team_members(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List all team members in the current tenant."""
    result = await db.execute(
        select(User).where(User.tenant_id == user.tenant_id).order_by(User.created_at)
    )
    members = result.scalars().all()
    return ok([
        {
            "id": str(m.id),
            "email": m.email,
            "full_name": m.full_name,
            "role": m.role,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in members
    ])


@router.patch("/team/{user_id}/role")
async def update_member_role(
    user_id: str,
    role: str,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_session),
):
    """Update a team member's role. Requires admin role."""
    import uuid as _uuid
    valid_roles = {"viewer", "accountant", "admin"}
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )
    result = await db.execute(
        select(User).where(User.id == _uuid.UUID(user_id), User.tenant_id == user.tenant_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change owner role")
    old_role = member.role
    member.role = role
    await db.commit()
    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        entity_type="team",
        entity_id=member.id,
        action="update_role",
        changes={"role": {"old": old_role, "new": role}},
    )
    return ok({"id": str(member.id), "email": member.email, "role": member.role})


@router.put("/company")
async def update_company(
    data: CompanySettingsUpdate,
    user: User = Depends(require_role("admin")),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Update company settings (TIN, RDO, etc.). Requires admin role."""
    repo = TenantRepository(db)
    updates = data.model_dump(exclude_none=True)
    if updates:
        # Build changes for audit
        changes = {}
        for key, new_val in updates.items():
            old_val = getattr(tenant, key, None)
            if str(old_val) != str(new_val):
                changes[key] = {"old": str(old_val) if old_val else None, "new": str(new_val)}

        tenant = await repo.update(tenant, **updates)

        if changes:
            await log_action(
                db,
                tenant_id=tenant.id,
                user_id=user.id,
                entity_type="company",
                entity_id=tenant.id,
                action="update",
                changes=changes,
            )

    return ok({
        "id": str(tenant.id),
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
        "vat_classification": tenant.vat_classification,
        "plan": tenant.plan,
    })
