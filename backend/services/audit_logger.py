"""Audit logging service for tracking all entity changes."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.audit import AuditRepository


async def log_action(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    entity_type: str,
    entity_id: uuid.UUID | None,
    action: str,
    changes: dict[str, Any] | None = None,
    comment: str | None = None,
) -> None:
    """Write an audit log entry.

    Args:
        db: Database session.
        tenant_id: Tenant performing the action.
        user_id: User performing the action.
        entity_type: Type of entity (report, preference, company, etc.).
        entity_id: ID of the affected entity.
        action: Action performed (create, update, delete, transition, etc.).
        changes: Dict of changed fields {field: {old: ..., new: ...}}.
        comment: Optional comment/reason for the action.
    """
    repo = AuditRepository(db)
    await repo.create(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changes=changes,
        comment=comment,
    )
