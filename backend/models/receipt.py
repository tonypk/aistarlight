"""Receipt batch model for OCR-based receipt processing."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, UUIDMixin


class ReceiptBatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "receipt_batches"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_images: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_sessions.id"), nullable=True
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True
    )
    report_type: Mapped[str] = mapped_column(String(20), default="BIR_2550M")
    period: Mapped[str] = mapped_column(String(20))
    results: Mapped[list | None] = mapped_column(JSONB, default=list)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
