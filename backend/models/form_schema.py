from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, UUIDMixin


class FormSchema(Base, UUIDMixin):
    __tablename__ = "form_schemas"

    form_type: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(200))
    frequency: Mapped[str] = mapped_column(String(20))  # monthly, quarterly, annual
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    schema_def: Mapped[dict] = mapped_column(JSONB)  # sections → fields
    calculation_rules: Mapped[dict] = mapped_column(JSONB)  # formula definitions
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
