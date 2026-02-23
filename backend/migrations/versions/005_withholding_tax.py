"""Add suppliers, withholding_certificates tables and EWT columns on transactions

Revision ID: 005_withholding_tax
Revises: 004_reconciliation
Create Date: 2026-02-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_withholding_tax"
down_revision: Union[str, None] = "004_reconciliation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- suppliers ---
    op.create_table(
        "suppliers",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column("tin", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("supplier_type", sa.String(20), server_default="corporation"),
        sa.Column("default_ewt_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("default_atc_code", sa.String(20), nullable=True),
        sa.Column("is_vat_registered", sa.Boolean, server_default="true"),
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
    op.create_index("ix_suppliers_tenant_id", "suppliers", ["tenant_id"])
    op.create_index("ix_suppliers_tin", "suppliers", ["tin"])

    # --- withholding_certificates ---
    op.create_table(
        "withholding_certificates",
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
            nullable=True,
        ),
        sa.Column(
            "supplier_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id"),
            nullable=False,
        ),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("quarter", sa.String(6), nullable=False),
        sa.Column("atc_code", sa.String(20), nullable=False),
        sa.Column("income_type", sa.String(100), nullable=False),
        sa.Column("income_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("ewt_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("tax_withheld", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("file_path", sa.Text, nullable=True),
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
    op.create_index("ix_withholding_certificates_tenant_id", "withholding_certificates", ["tenant_id"])
    op.create_index("ix_withholding_certificates_supplier_id", "withholding_certificates", ["supplier_id"])

    # --- Add EWT columns to transactions ---
    op.add_column("transactions", sa.Column("ewt_rate", sa.Numeric(5, 4), nullable=True))
    op.add_column("transactions", sa.Column("ewt_amount", sa.Numeric(15, 2), nullable=True))
    op.add_column("transactions", sa.Column("atc_code", sa.String(20), nullable=True))
    op.add_column(
        "transactions",
        sa.Column(
            "supplier_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Remove EWT columns from transactions
    op.drop_column("transactions", "supplier_id")
    op.drop_column("transactions", "atc_code")
    op.drop_column("transactions", "ewt_amount")
    op.drop_column("transactions", "ewt_rate")

    # Drop withholding_certificates
    op.drop_index("ix_withholding_certificates_supplier_id", table_name="withholding_certificates")
    op.drop_index("ix_withholding_certificates_tenant_id", table_name="withholding_certificates")
    op.drop_table("withholding_certificates")

    # Drop suppliers
    op.drop_index("ix_suppliers_tin", table_name="suppliers")
    op.drop_index("ix_suppliers_tenant_id", table_name="suppliers")
    op.drop_table("suppliers")
