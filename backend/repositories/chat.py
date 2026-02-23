import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.chat import ChatMessage
from backend.repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(ChatMessage, session)

    async def find_by_tenant(
        self,
        tenant_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ChatMessage]:
        query = (
            select(ChatMessage)
            .where(ChatMessage.tenant_id == tenant_id)
            .order_by(desc(ChatMessage.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(reversed(result.scalars().all()))

    async def create_message(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        content: str,
        tool_calls: dict | None = None,
    ) -> ChatMessage:
        return await self.create(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
        )
