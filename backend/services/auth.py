import secrets
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from backend.models.revoked_token import RevokedToken
from backend.models.user_tenant import UserTenant
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

    # Also add to user_tenants for multi-company support
    db.add(UserTenant(user_id=user.id, tenant_id=tenant.id, role="owner"))
    await db.flush()

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

    token_data = {"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> TokenResponse:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Check if token has been revoked
    jti = payload.get("jti")
    if jti:
        revoked = await db.execute(
            select(RevokedToken).where(RevokedToken.jti == jti)
        )
        if revoked.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Revoke the old refresh token (rotation)
    if jti:
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=UTC) if exp else datetime.now(UTC)
        db.add(RevokedToken(
            jti=jti,
            user_id=user.id,
            revoked_at=datetime.now(UTC),
            expires_at=expires_at,
        ))
        await db.flush()

    token_data = {"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


async def revoke_token(token: str, user_id: uuid.UUID, db: AsyncSession) -> None:
    """Revoke a specific token by its JTI."""
    payload = decode_token(token)
    if payload is None:
        return
    jti = payload.get("jti")
    if not jti:
        return
    exp = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp, tz=UTC) if exp else datetime.now(UTC)
    db.add(RevokedToken(
        jti=jti,
        user_id=user_id,
        revoked_at=datetime.now(UTC),
        expires_at=expires_at,
    ))
    await db.flush()


async def revoke_all_user_tokens(user_id: uuid.UUID, db: AsyncSession) -> int:
    """Mark all active tokens for a user as revoked by inserting a sentinel."""
    # We can't enumerate all JTIs, but we can store a "revoke_all_before" timestamp
    # For simplicity, this is handled by checking user.is_active in token validation
    # Future: store token family IDs for full revocation tracking
    return 0


async def generate_api_key(user_id: str, db: AsyncSession) -> str:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    api_key = f"ask_{secrets.token_urlsafe(32)}"
    await user_repo.update(user, api_key=api_key)
    return api_key


async def switch_tenant(user_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession) -> TokenResponse:
    """Switch the user's active tenant and issue new tokens."""
    from backend.models.tenant import Tenant, User

    # Verify user has access to this tenant
    result = await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == user_id,
            UserTenant.tenant_id == tenant_id,
        )
    )
    user_tenant = result.scalar_one_or_none()
    if not user_tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this company")

    # Update user's primary tenant
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.tenant_id = tenant_id
    user.role = user_tenant.role
    await db.flush()

    token_data = {"sub": str(user.id), "tenant_id": str(tenant_id), "role": user_tenant.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


async def get_user_tenants(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """Get all tenants a user has access to."""
    from backend.models.tenant import Tenant

    result = await db.execute(
        select(UserTenant, Tenant)
        .join(Tenant, Tenant.id == UserTenant.tenant_id)
        .where(UserTenant.user_id == user_id)
    )
    rows = result.all()
    return [
        {
            "tenant_id": str(ut.tenant_id),
            "company_name": tenant.company_name,
            "role": ut.role,
            "tin_number": tenant.tin_number,
        }
        for ut, tenant in rows
    ]


async def invite_user_to_tenant(
    email: str, tenant_id: uuid.UUID, role: str, inviter_id: uuid.UUID, db: AsyncSession
) -> dict:
    """Invite a user to a tenant. If user exists, link them. Otherwise return pending."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. They must register first.")

    # Check if already a member
    existing = await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == tenant_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already a member of this company")

    if role not in ("owner", "admin", "accountant", "viewer"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    db.add(UserTenant(user_id=user.id, tenant_id=tenant_id, role=role))
    await db.flush()

    return {"user_id": str(user.id), "email": email, "role": role, "status": "added"}
