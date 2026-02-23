"""Bank reconciliation batch model."""

import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, UUIDMixin


class BankReconciliationBatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bank_reconciliation_batches"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reconciliation_sessions.id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    source_files: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_entries: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    parse_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    match_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_suggestions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_explanations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    amount_tolerance: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False, server_default="0.01"
    )
    date_tolerance_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="3"
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
