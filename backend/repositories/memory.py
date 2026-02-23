import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.memory import CorrectionHistory, UserPreference
from backend.repositories.base import BaseRepository


class PreferenceRepository(BaseRepository[UserPreference]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserPreference, session)

    async def get_by_tenant_and_type(
        self, tenant_id: uuid.UUID, report_type: str
    ) -> UserPreference | None:
        result = await self.session.execute(
            select(UserPreference).where(
                UserPreference.tenant_id == tenant_id,
                UserPreference.report_type == report_type,
            )
        )
        return result.scalar_one_or_none()

    async def find_by_tenant(self, tenant_id: uuid.UUID) -> list[UserPreference]:
        result = await self.session.execute(
            select(UserPreference).where(UserPreference.tenant_id == tenant_id)
        )
        return list(result.scalars().all())


class CorrectionRepository(BaseRepository[CorrectionHistory]):
    def __init__(self, session: AsyncSession):
        super().__init__(CorrectionHistory, session)

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[CorrectionHistory]:
        result = await self.session.execute(
            select(CorrectionHistory)
            .where(CorrectionHistory.tenant_id == tenant_id)
            .order_by(CorrectionHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
