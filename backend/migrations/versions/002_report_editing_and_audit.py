"""Report editing fields + audit_logs table

Revision ID: 002_report_editing_and_audit
Revises: 001_initial
Create Date: 2026-02-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_report_editing_and_audit"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- audit_logs table ---
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changes", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # --- reports table extensions (all nullable or have defaults → no lock) ---
    op.add_column(
        "reports",
        sa.Column(
            "created_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "reports",
        sa.Column(
            "updated_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "reports",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.add_column(
        "reports",
        sa.Column("overrides", sa.dialects.postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column("original_calculated_data", sa.dialects.postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column("notes", sa.Text, nullable=True),
    )

    # Backfill: snapshot current calculated_data as original
    op.execute(
        "UPDATE reports SET original_calculated_data = calculated_data WHERE original_calculated_data IS NULL"
    )


def downgrade() -> None:
    op.drop_column("reports", "notes")
    op.drop_column("reports", "original_calculated_data")
    op.drop_column("reports", "overrides")
    op.drop_column("reports", "version")
    op.drop_column("reports", "updated_at")
    op.drop_column("reports", "updated_by")
    op.drop_column("reports", "created_by")

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_table("audit_logs")
