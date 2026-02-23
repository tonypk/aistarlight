"""Supplier model for withholding tax management."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin, UUIDMixin


class Supplier(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "suppliers"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True
    )
    tin: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_type: Mapped[str] = mapped_column(String(20), default="corporation")
    default_ewt_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    default_atc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_vat_registered: Mapped[bool] = mapped_column(Boolean, default=True)
