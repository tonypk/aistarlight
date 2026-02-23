"""receipt batches table

Revision ID: 007
Revises: 006
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "receipt_batches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_images", sa.Integer, nullable=False, server_default="0"),
        sa.Column("processed_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("reconciliation_sessions.id"), nullable=True),
        sa.Column("report_id", UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=True),
        sa.Column("report_type", sa.String(20), nullable=False, server_default="BIR_2550M"),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("results", JSONB, nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("receipt_batches")
