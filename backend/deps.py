import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.database import get_db
from backend.core.security import decode_token
from backend.models.tenant import Tenant, User

security = HTTPBearer(auto_error=False)

# Role hierarchy: owner > admin > accountant > viewer
ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "accountant": 2,
    "viewer": 1,
}


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Authenticate via JWT Bearer token or API Key."""
    # Try API Key first
    if x_api_key:
        result = await db.execute(select(User).where(User.api_key == x_api_key, User.is_active))
        user = result.scalar_one_or_none()
        if user:
            return user

    # Try JWT
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


async def get_current_tenant(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


def require_role(minimum_role: str):
    """Dependency factory that checks if the current user has at least the given role.

    Usage:
        @router.post("/admin-action")
        async def admin_action(user: User = Depends(require_role("admin"))):
            ...
    """
    min_level = ROLE_HIERARCHY.get(minimum_role, 0)

    async def _check_role(user: User = Depends(get_current_user)) -> User:
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {minimum_role} role or higher",
            )
        return user

    return _check_role
