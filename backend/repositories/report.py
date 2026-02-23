import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.report import Report
from backend.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session: AsyncSession):
        super().__init__(Report, session)

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> list[Report]:
        result = await self.session.execute(
            select(Report)
            .where(Report.tenant_id == tenant_id)
            .order_by(Report.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_period(self, tenant_id: uuid.UUID, report_type: str, period: str) -> Report | None:
        result = await self.session.execute(
            select(Report).where(
                Report.tenant_id == tenant_id,
                Report.report_type == report_type,
                Report.period == period,
            )
        )
        return result.scalar_one_or_none()
