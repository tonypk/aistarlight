"""Repository for transactions."""

import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.transaction import Transaction
from backend.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(Transaction, session)

    async def find_by_session(
        self,
        session_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[Transaction]:
        query = select(Transaction).where(Transaction.session_id == session_id)
        if filters:
            if filters.get("vat_type"):
                query = query.where(Transaction.vat_type == filters["vat_type"])
            if filters.get("category"):
                query = query.where(Transaction.category == filters["category"])
            if filters.get("source_type"):
                query = query.where(Transaction.source_type == filters["source_type"])
            if filters.get("match_status"):
                query = query.where(Transaction.match_status == filters["match_status"])
            if filters.get("min_confidence") is not None:
                query = query.where(Transaction.confidence >= filters["min_confidence"])
            if filters.get("search"):
                query = query.where(Transaction.description.ilike(f"%{filters['search']}%"))
        query = query.order_by(Transaction.row_index).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_session(
        self, session_id: uuid.UUID, filters: dict[str, Any] | None = None
    ) -> int:
        query = select(func.count()).select_from(Transaction).where(
            Transaction.session_id == session_id
        )
        if filters:
            if filters.get("vat_type"):
                query = query.where(Transaction.vat_type == filters["vat_type"])
            if filters.get("category"):
                query = query.where(Transaction.category == filters["category"])
            if filters.get("source_type"):
                query = query.where(Transaction.source_type == filters["source_type"])
        result = await self.session.execute(query)
        return result.scalar_one()

    async def find_all_by_session(self, session_id: uuid.UUID) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.session_id == session_id)
            .order_by(Transaction.row_index)
        )
        return list(result.scalars().all())

    async def bulk_create(self, transactions: list[dict]) -> list[Transaction]:
        instances = [Transaction(**data) for data in transactions]
        self.session.add_all(instances)
        await self.session.flush()
        return instances
