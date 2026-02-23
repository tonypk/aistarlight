"""bank reconciliation batches table

Revision ID: 008_bank_reconciliation
Revises: 007_receipt_batches
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "008_bank_reconciliation"
down_revision = "007_receipt_batches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_reconciliation_batches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("reconciliation_sessions.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("source_files", JSONB, nullable=True),
        sa.Column("total_entries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("parse_summary", JSONB, nullable=True),
        sa.Column("match_result", JSONB, nullable=True),
        sa.Column("ai_suggestions", JSONB, nullable=True),
        sa.Column("ai_explanations", JSONB, nullable=True),
        sa.Column("amount_tolerance", sa.Numeric(10, 4), nullable=False, server_default="0.01"),
        sa.Column("date_tolerance_days", sa.Integer, nullable=False, server_default="3"),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("bank_reconciliation_batches")
