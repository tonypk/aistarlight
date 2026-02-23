"""One-time script to create chat_messages table if it doesn't exist."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from backend.core.database import async_session_factory


async def main():
    async with async_session_factory() as session:
        await session.execute(text(
            "CREATE TABLE IF NOT EXISTS chat_messages ("
            "  id UUID PRIMARY KEY,"
            "  tenant_id UUID NOT NULL REFERENCES tenants(id),"
            "  user_id UUID NOT NULL REFERENCES users(id),"
            "  role VARCHAR(20) NOT NULL,"
            "  content TEXT NOT NULL,"
            "  tool_calls JSONB,"
            "  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL"
            ")"
        ))
        await session.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_chat_messages_tenant_id ON chat_messages(tenant_id)"
        ))
        await session.commit()
        print("chat_messages table created successfully")


if __name__ == "__main__":
    asyncio.run(main())
