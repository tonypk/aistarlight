from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, UUIDMixin


class KnowledgeChunk(Base, UUIDMixin):
    __tablename__ = "knowledge_chunks"

    source: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1024))  # Claude embedding dimension
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Note: hnsw index will be created via migration when data exists
    # ivfflat requires data to build, hnsw does not but is expensive on empty table
    __table_args__: tuple = ()
