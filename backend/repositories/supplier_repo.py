"""Repository for suppliers."""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.supplier import Supplier
from backend.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, session: AsyncSession):
        super().__init__(Supplier, session)

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Supplier]:
        result = await self.session.execute(
            select(Supplier)
            .where(Supplier.tenant_id == tenant_id)
            .order_by(Supplier.name)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_tin(self, tenant_id: uuid.UUID, tin: str) -> Supplier | None:
        result = await self.session.execute(
            select(Supplier)
            .where(Supplier.tenant_id == tenant_id, Supplier.tin == tin)
        )
        return result.scalar_one_or_none()

    async def search(
        self, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[Supplier]:
        result = await self.session.execute(
            select(Supplier)
            .where(
                Supplier.tenant_id == tenant_id,
                (Supplier.name.ilike(f"%{query}%")) | (Supplier.tin.ilike(f"%{query}%")),
            )
            .order_by(Supplier.name)
            .limit(limit)
        )
        return list(result.scalars().all())
