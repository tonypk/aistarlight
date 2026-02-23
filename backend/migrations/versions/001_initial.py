"""Initial migration: all tables + pgvector extension

Revision ID: 001_initial
Revises:
Create Date: 2026-02-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Tenants
    op.create_table(
        "tenants",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("tin_number", sa.String(20), nullable=True),
        sa.Column("rdo_code", sa.String(10), nullable=True),
        sa.Column("vat_classification", sa.String(20), nullable=False, server_default="vat_registered"),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="owner"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("api_key", sa.String(64), nullable=True, unique=True),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_api_key", "users", ["api_key"])

    # Reports
    op.create_table(
        "reports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("input_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("calculated_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # User Preferences
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("column_mappings", sa.dialects.postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("format_rules", sa.dialects.postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("auto_fill_rules", sa.dialects.postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "report_type"),
    )

    # Correction History
    op.create_table(
        "correction_history",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=True),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Knowledge Chunks
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("metadata", sa.dialects.postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Chat Messages
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tool_calls", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_messages_tenant_id", "chat_messages", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("knowledge_chunks")
    op.drop_table("correction_history")
    op.drop_table("user_preferences")
    op.drop_table("reports")
    op.drop_table("users")
    op.drop_table("tenants")
    op.execute("DROP EXTENSION IF EXISTS vector")
