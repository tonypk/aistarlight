"""Repository for bank reconciliation batches."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bank_recon import BankReconciliationBatch
from backend.repositories.base import BaseRepository


class BankReconBatchRepository(BaseRepository[BankReconciliationBatch]):
    def __init__(self, session: AsyncSession):
        super().__init__(BankReconciliationBatch, session)

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> list[BankReconciliationBatch]:
        result = await self.session.execute(
            select(BankReconciliationBatch)
            .where(BankReconciliationBatch.tenant_id == tenant_id)
            .order_by(BankReconciliationBatch.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_session(
        self, session_id: uuid.UUID
    ) -> list[BankReconciliationBatch]:
        result = await self.session.execute(
            select(BankReconciliationBatch)
            .where(BankReconciliationBatch.session_id == session_id)
            .order_by(BankReconciliationBatch.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_tenant(self, tenant_id: uuid.UUID) -> int:
        return await self.count(tenant_id=tenant_id)
