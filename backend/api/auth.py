from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from backend.schemas.common import ok
from backend.services.auth import generate_api_key, login_user, refresh_access_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_session)):
    user = await register_user(data, db)
    return ok(user.model_dump())


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_session)):
    tokens = await login_user(data, db)
    return ok(tokens.model_dump())


@router.post("/refresh")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_session)):
    tokens = await refresh_access_token(data.refresh_token, db)
    return ok(tokens.model_dump())


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
