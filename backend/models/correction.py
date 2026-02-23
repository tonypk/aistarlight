"""Models for correction tracking, learned rules, and validation results."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, UUIDMixin


class Correction(Base, UUIDMixin):
    """Record of an accountant's correction to a classification or report field."""

    __tablename__ = "corrections"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    field_name: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    new_value: Mapped[str] = mapped_column(String(500))
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    context_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        server_default=func.now(),
    )


class CorrectionRule(Base, UUIDMixin):
    """A learned rule derived from repeated correction patterns."""

    __tablename__ = "correction_rules"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True
    )
    rule_type: Mapped[str] = mapped_column(String(30))
    match_criteria: Mapped[dict] = mapped_column(JSONB)
    correction_field: Mapped[str] = mapped_column(String(100))
    correction_value: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0.85)
    source_correction_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        server_default=func.now(),
    )


class ValidationResult(Base, UUIDMixin):
    """Result of a compliance validation run against a report."""

    __tablename__ = "validation_results"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True
    )
    overall_score: Mapped[int] = mapped_column(Integer)
    check_results: Mapped[dict] = mapped_column(JSONB)
    rag_findings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        server_default=func.now(),
    )
