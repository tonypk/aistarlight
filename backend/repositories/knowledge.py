from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.knowledge import KnowledgeChunk
from backend.repositories.base import BaseRepository


class KnowledgeRepository(BaseRepository[KnowledgeChunk]):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeChunk, session)

    async def search_similar(
        self, embedding: list[float], category: str | None = None, limit: int = 5
    ) -> list[KnowledgeChunk]:
        query = (
            select(KnowledgeChunk)
            .order_by(KnowledgeChunk.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        if category:
            query = query.where(KnowledgeChunk.category == category)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_by_category(self, category: str) -> list[KnowledgeChunk]:
        result = await self.session.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.category == category)
        )
        return list(result.scalars().all())
