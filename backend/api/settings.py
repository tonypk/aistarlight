from fastapi import APIRouter, Depends
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
