import secrets

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from backend.repositories.tenant import TenantRepository, UserRepository
from backend.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


async def register_user(data: RegisterRequest, db: AsyncSession) -> UserResponse:
    user_repo = UserRepository(db)
    tenant_repo = TenantRepository(db)

    existing = await user_repo.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    tenant = await tenant_repo.create(company_name=data.company_name)
    user = await user_repo.create(
        tenant_id=tenant.id,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role="owner",
    )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=str(tenant.id),
        company_name=tenant.company_name,
    )


async def login_user(data: LoginRequest, db: AsyncSession) -> TokenResponse:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(data.email)

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token_data = {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> TokenResponse:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_repo = UserRepository(db)
    import uuid
    user = await user_repo.get_by_id(uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token_data = {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


async def generate_api_key(user_id: str, db: AsyncSession) -> str:
    user_repo = UserRepository(db)
    import uuid
    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    api_key = f"ask_{secrets.token_urlsafe(32)}"
    await user_repo.update(user, api_key=api_key)
    return api_key
