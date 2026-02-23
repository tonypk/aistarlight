"""Add corrections, correction_rules, validation_results tables and compliance_score column

Revision ID: 006_corrections_and_validation
Revises: 005_withholding_tax
Create Date: 2026-02-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_corrections_and_validation"
down_revision: Union[str, None] = "005_withholding_tax"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- corrections ---
    op.create_table(
        "corrections",
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
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("old_value", sa.String(500), nullable=True),
        sa.Column("new_value", sa.String(500), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("context_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_corrections_tenant_id", "corrections", ["tenant_id"])
    op.create_index("ix_corrections_entity", "corrections", ["entity_type", "entity_id"])
    op.create_index("ix_corrections_field", "corrections", ["field_name"])

    # --- correction_rules ---
    op.create_table(
        "correction_rules",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column("rule_type", sa.String(30), nullable=False),
        sa.Column("match_criteria", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("correction_field", sa.String(100), nullable=False),
        sa.Column("correction_value", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), server_default="0.85"),
        sa.Column("source_correction_count", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
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
    op.create_index("ix_correction_rules_tenant_id", "correction_rules", ["tenant_id"])
    op.create_index("ix_correction_rules_active", "correction_rules", ["tenant_id", "is_active"])

    # --- validation_results ---
    op.create_table(
        "validation_results",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "report_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reports.id"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column("overall_score", sa.Integer, nullable=False),
        sa.Column("check_results", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("rag_findings", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "validated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_validation_results_report_id", "validation_results", ["report_id"])
    op.create_index("ix_validation_results_tenant_id", "validation_results", ["tenant_id"])

    # --- Add compliance_score to reports ---
    op.add_column("reports", sa.Column("compliance_score", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "compliance_score")

    op.drop_index("ix_validation_results_tenant_id", table_name="validation_results")
    op.drop_index("ix_validation_results_report_id", table_name="validation_results")
    op.drop_table("validation_results")

    op.drop_index("ix_correction_rules_active", table_name="correction_rules")
    op.drop_index("ix_correction_rules_tenant_id", table_name="correction_rules")
    op.drop_table("correction_rules")

    op.drop_index("ix_corrections_field", table_name="corrections")
    op.drop_index("ix_corrections_entity", table_name="corrections")
    op.drop_index("ix_corrections_tenant_id", table_name="corrections")
    op.drop_table("corrections")
