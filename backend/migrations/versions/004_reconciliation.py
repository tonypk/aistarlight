"""Add reconciliation_sessions, transactions, anomalies tables

Revision ID: 004_reconciliation
Revises: 003_form_schema_registry
Create Date: 2026-02-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_reconciliation"
down_revision: Union[str, None] = "003_form_schema_registry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- reconciliation_sessions ---
    op.create_table(
        "reconciliation_sessions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "report_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reports.id"),
            nullable=True,
        ),
        sa.Column("source_files", sa.dialects.postgresql.JSONB, server_default="[]"),
        sa.Column("summary", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("reconciliation_result", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index(
        "ix_reconciliation_sessions_tenant_id",
        "reconciliation_sessions",
        ["tenant_id"],
    )

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reconciliation_sessions.id"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_file_id", sa.String(36), nullable=False),
        sa.Column("row_index", sa.Integer, nullable=False),
        sa.Column("date", sa.Date, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("vat_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("vat_type", sa.String(20), server_default="vatable"),
        sa.Column("category", sa.String(20), server_default="goods"),
        sa.Column("tin", sa.String(20), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), server_default="0"),
        sa.Column("classification_source", sa.String(20), server_default="ai"),
        sa.Column("raw_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "match_group_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("match_status", sa.String(20), server_default="unmatched"),
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
    op.create_index("ix_transactions_tenant_id", "transactions", ["tenant_id"])
    op.create_index("ix_transactions_session_id", "transactions", ["session_id"])

    # --- anomalies ---
    op.create_table(
        "anomalies",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reconciliation_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id"),
            nullable=True,
        ),
        sa.Column("anomaly_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("details", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), server_default="open"),
        sa.Column(
            "resolved_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text, nullable=True),
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
    op.create_index("ix_anomalies_tenant_id", "anomalies", ["tenant_id"])
    op.create_index("ix_anomalies_session_id", "anomalies", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_anomalies_session_id", table_name="anomalies")
    op.drop_index("ix_anomalies_tenant_id", table_name="anomalies")
    op.drop_table("anomalies")

    op.drop_index("ix_transactions_session_id", table_name="transactions")
    op.drop_index("ix_transactions_tenant_id", table_name="transactions")
    op.drop_table("transactions")

    op.drop_index(
        "ix_reconciliation_sessions_tenant_id",
        table_name="reconciliation_sessions",
    )
    op.drop_table("reconciliation_sessions")
