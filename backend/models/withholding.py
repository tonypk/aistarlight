"""Withholding certificate model for BIR 2307."""

import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, UUIDMixin


class WithholdingCertificate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "withholding_certificates"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_sessions.id"), nullable=True
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), index=True
    )
    period: Mapped[str] = mapped_column(String(20))
    quarter: Mapped[str] = mapped_column(String(6))
    atc_code: Mapped[str] = mapped_column(String(20))
    income_type: Mapped[str] = mapped_column(String(100))
    income_amount: Mapped[float] = mapped_column(Numeric(15, 2))
    ewt_rate: Mapped[float] = mapped_column(Numeric(5, 4))
    tax_withheld: Mapped[float] = mapped_column(Numeric(15, 2))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
