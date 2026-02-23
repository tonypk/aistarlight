"""Transaction model for classified financial records."""

import uuid
from datetime import date as date_type

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, UUIDMixin


class Transaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transactions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_sessions.id"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(20))
    source_file_id: Mapped[str] = mapped_column(String(36))
    row_index: Mapped[int] = mapped_column(Integer)
    date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 2))
    vat_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    vat_type: Mapped[str] = mapped_column(String(20), default="vatable")
    category: Mapped[str] = mapped_column(String(20), default="goods")
    tin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    classification_source: Mapped[str] = mapped_column(String(20), default="ai")
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    match_group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    match_status: Mapped[str] = mapped_column(String(20), default="unmatched")

    # Withholding tax fields
    ewt_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    ewt_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    atc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
