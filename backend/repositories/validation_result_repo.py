"""Repository for compliance validation results."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.correction import ValidationResult
from backend.repositories.base import BaseRepository


class ValidationResultRepository(BaseRepository[ValidationResult]):
    def __init__(self, session: AsyncSession):
        super().__init__(ValidationResult, session)

    async def find_by_report(
        self, report_id: uuid.UUID, limit: int = 10
    ) -> list[ValidationResult]:
        query = (
            select(ValidationResult)
            .where(ValidationResult.report_id == report_id)
            .order_by(ValidationResult.validated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_latest_by_report(
        self, report_id: uuid.UUID
    ) -> ValidationResult | None:
        query = (
            select(ValidationResult)
            .where(ValidationResult.report_id == report_id)
            .order_by(ValidationResult.validated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
