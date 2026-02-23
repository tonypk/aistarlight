"""Form schema registry table

Revision ID: 003_form_schema_registry
Revises: 002_report_editing_and_audit
Create Date: 2026-02-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_form_schema_registry"
down_revision: Union[str, None] = "002_report_editing_and_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "form_schemas",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("form_type", sa.String(30), nullable=False, unique=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("schema_def", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("calculation_rules", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_form_schemas_form_type", "form_schemas", ["form_type"])


def downgrade() -> None:
    op.drop_index("ix_form_schemas_form_type", table_name="form_schemas")
    op.drop_table("form_schemas")
