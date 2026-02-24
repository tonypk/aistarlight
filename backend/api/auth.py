import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from backend.schemas.common import ok
from backend.services.auth import (
    generate_api_key,
    get_user_tenants,
    invite_user_to_tenant,
    login_user,
    refresh_access_token,
    register_user,
    revoke_token,
    switch_tenant,
)

router = APIRouter(prefix="/auth", tags=["auth"])
auth_limiter = Limiter(key_func=get_remote_address)


@router.post("/register")
@auth_limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_session)):
    user = await register_user(data, db)
    return ok(user.model_dump())


@router.post("/login")
@auth_limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_session)):
    tokens = await login_user(data, db)
    return ok(tokens.model_dump())


@router.post("/refresh")
@auth_limiter.limit("20/minute")
async def refresh(request: Request, data: RefreshRequest, db: AsyncSession = Depends(get_session)):
    tokens = await refresh_access_token(data.refresh_token, db)
    return ok(tokens.model_dump())


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout")
async def logout(
    data: LogoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Revoke the refresh token on logout."""
    await revoke_token(data.refresh_token, user.id, db)
    return ok({"message": "Logged out successfully"})


@router.get("/me")
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    from sqlalchemy import select

    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one()
    return ok(
        UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=str(user.tenant_id),
            company_name=tenant.company_name,
        ).model_dump()
    )


@router.post("/api-key")
async def create_api_key(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Generate an API key for programmatic access."""
    key = await generate_api_key(str(user.id), db)
    return ok({"api_key": key})


# --- Multi-Company Endpoints ---

@router.get("/companies")
async def list_companies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List all companies the current user has access to."""
    tenants = await get_user_tenants(user.id, db)
    return ok({"companies": tenants, "current_tenant_id": str(user.tenant_id)})


class SwitchCompanyRequest(BaseModel):
    tenant_id: str


@router.post("/switch-company")
async def switch_company(
    data: SwitchCompanyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Switch active company and get new tokens."""
    tokens = await switch_tenant(user.id, uuid.UUID(data.tenant_id), db)
    return ok(tokens.model_dump())


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "viewer"


@router.post("/invite")
async def invite_member(
    data: InviteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Invite a user to the current company. Only owner/admin can invite."""
    if user.role not in ("owner", "admin"):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner/admin can invite members")
    result = await invite_user_to_tenant(data.email, user.tenant_id, data.role, user.id, db)
    return ok(result)
