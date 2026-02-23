from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_tenant, get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.repositories.tenant import TenantRepository
from backend.schemas.common import ok
from backend.schemas.tenant import CompanySettingsUpdate

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
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Update company settings (TIN, RDO, etc.)."""
    repo = TenantRepository(db)
    updates = data.model_dump(exclude_none=True)
    if updates:
        tenant = await repo.update(tenant, **updates)
    return ok({
        "id": str(tenant.id),
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
        "vat_classification": tenant.vat_classification,
        "plan": tenant.plan,
    })
