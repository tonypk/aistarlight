"""Repository for correction records."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.correction import Correction
from backend.repositories.base import BaseRepository


class CorrectionRepository(BaseRepository[Correction]):
    def __init__(self, session: AsyncSession):
        super().__init__(Correction, session)

    async def find_by_entity(
        self, entity_type: str, entity_id: uuid.UUID
    ) -> list[Correction]:
        query = (
            select(Correction)
            .where(
                and_(
                    Correction.entity_type == entity_type,
                    Correction.entity_id == entity_id,
                )
            )
            .order_by(Correction.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_by_tenant(
        self,
        tenant_id: uuid.UUID,
        entity_type: str | None = None,
        field_name: str | None = None,
        since: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Correction]:
        query = select(Correction).where(Correction.tenant_id == tenant_id)
        if entity_type:
            query = query.where(Correction.entity_type == entity_type)
        if field_name:
            query = query.where(Correction.field_name == field_name)
        if since:
            query = query.where(Correction.created_at >= since)
        query = query.order_by(Correction.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_tenant(
        self,
        tenant_id: uuid.UUID,
        entity_type: str | None = None,
        field_name: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(Correction).where(
            Correction.tenant_id == tenant_id
        )
        if entity_type:
            query = query.where(Correction.entity_type == entity_type)
        if field_name:
            query = query.where(Correction.field_name == field_name)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def find_by_field_pattern(
        self,
        tenant_id: uuid.UUID,
        field_name: str,
        new_value: str,
    ) -> list[Correction]:
        """Find corrections with the same field+value pattern (for rule learning)."""
        query = (
            select(Correction)
            .where(
                and_(
                    Correction.tenant_id == tenant_id,
                    Correction.field_name == field_name,
                    Correction.new_value == new_value,
                )
            )
            .order_by(Correction.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_correction_stats(
        self, tenant_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """Get correction counts grouped by field_name and new_value."""
        query = (
            select(
                Correction.field_name,
                Correction.new_value,
                Correction.entity_type,
                func.count().label("count"),
            )
            .where(Correction.tenant_id == tenant_id)
            .group_by(Correction.field_name, Correction.new_value, Correction.entity_type)
            .order_by(func.count().desc())
        )
        result = await self.session.execute(query)
        return [
            {
                "field_name": row.field_name,
                "new_value": row.new_value,
                "entity_type": row.entity_type,
                "count": row.count,
            }
            for row in result.all()
        ]
