"""Repository for receipt batches."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.receipt import ReceiptBatch
from backend.repositories.base import BaseRepository


class ReceiptBatchRepository(BaseRepository[ReceiptBatch]):
    def __init__(self, session: AsyncSession):
        super().__init__(ReceiptBatch, session)

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> list[ReceiptBatch]:
        result = await self.session.execute(
            select(ReceiptBatch)
            .where(ReceiptBatch.tenant_id == tenant_id)
            .order_by(ReceiptBatch.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
