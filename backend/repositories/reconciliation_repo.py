"""Repository for reconciliation sessions."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.reconciliation import ReconciliationSession
from backend.repositories.base import BaseRepository


class ReconciliationSessionRepository(BaseRepository[ReconciliationSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(ReconciliationSession, session)

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> list[ReconciliationSession]:
        result = await self.session.execute(
            select(ReconciliationSession)
            .where(ReconciliationSession.tenant_id == tenant_id)
            .order_by(ReconciliationSession.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
