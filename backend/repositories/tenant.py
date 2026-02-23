from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tenant import Tenant, User
from backend.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_api_key(self, api_key: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.api_key == api_key, User.is_active)
        )
        return result.scalar_one_or_none()
