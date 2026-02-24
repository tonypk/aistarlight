"""RBAC, multi-company support, and token revocation

Revision ID: 009_rbac_multicompany_tokens
Revises: 008_bank_reconciliation
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "009_rbac_multicompany_tokens"
down_revision = "008_bank_reconciliation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Revoked tokens table for JWT revocation
    op.create_table(
        "revoked_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("jti", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # User-tenant many-to-many for multi-company access
    op.create_table(
        "user_tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant"),
    )

    # Backfill: copy existing user-tenant relationships into user_tenants
    op.execute("""
        INSERT INTO user_tenants (id, user_id, tenant_id, role, joined_at)
        SELECT gen_random_uuid(), id, tenant_id, role, now()
        FROM users
        WHERE tenant_id IS NOT NULL
        ON CONFLICT (user_id, tenant_id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("user_tenants")
    op.drop_table("revoked_tokens")
