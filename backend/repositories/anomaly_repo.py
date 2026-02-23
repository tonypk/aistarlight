"""Repository for anomalies."""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.anomaly import Anomaly
from backend.repositories.base import BaseRepository


class AnomalyRepository(BaseRepository[Anomaly]):
    def __init__(self, session: AsyncSession):
        super().__init__(Anomaly, session)

    async def find_by_session(
        self,
        session_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
        status_filter: str | None = None,
    ) -> list[Anomaly]:
        query = select(Anomaly).where(Anomaly.session_id == session_id)
        if status_filter:
            query = query.where(Anomaly.status == status_filter)
        query = query.order_by(Anomaly.severity, Anomaly.created_at).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_session(
        self, session_id: uuid.UUID, status_filter: str | None = None
    ) -> int:
        query = select(func.count()).select_from(Anomaly).where(
            Anomaly.session_id == session_id
        )
        if status_filter:
            query = query.where(Anomaly.status == status_filter)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def bulk_create(self, anomalies: list[dict]) -> list[Anomaly]:
        instances = [Anomaly(**data) for data in anomalies]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    async def delete_by_session(self, session_id: uuid.UUID) -> int:
        from sqlalchemy import delete
        result = await self.session.execute(
            delete(Anomaly).where(Anomaly.session_id == session_id)
        )
        return result.rowcount
