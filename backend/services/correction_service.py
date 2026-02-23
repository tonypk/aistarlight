"""Service for recording and querying accountant corrections.

Captures context snapshots from the corrected entity for pattern learning.
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.correction import Correction
from backend.models.transaction import Transaction
from backend.models.report import Report
from backend.repositories.correction_repo import CorrectionRepository
from backend.services.audit_logger import log_action

logger = logging.getLogger(__name__)


async def _build_context_snapshot(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
) -> dict | None:
    """Build a context snapshot from the entity being corrected."""
    if entity_type == "transaction_classification":
        result = await db.execute(
            select(Transaction).where(Transaction.id == entity_id)
        )
        txn = result.scalar_one_or_none()
        if txn:
            return {
                "description": txn.description,
                "amount": float(txn.amount),
                "tin": txn.tin,
                "source_type": txn.source_type,
                "vat_type": txn.vat_type,
                "category": txn.category,
                "confidence": float(txn.confidence),
                "classification_source": txn.classification_source,
                "atc_code": txn.atc_code,
            }
    elif entity_type == "report_field":
        result = await db.execute(
            select(Report).where(Report.id == entity_id)
        )
        report = result.scalar_one_or_none()
        if report:
            return {
                "report_type": report.report_type,
                "period": report.period,
                "status": report.status,
            }
    elif entity_type == "ewt_classification":
        result = await db.execute(
            select(Transaction).where(Transaction.id == entity_id)
        )
        txn = result.scalar_one_or_none()
        if txn:
            return {
                "description": txn.description,
                "amount": float(txn.amount),
                "tin": txn.tin,
                "ewt_rate": float(txn.ewt_rate) if txn.ewt_rate else None,
                "atc_code": txn.atc_code,
                "supplier_id": str(txn.supplier_id) if txn.supplier_id else None,
            }
    return None


async def record_correction(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    field_name: str,
    old_value: str | None,
    new_value: str,
    reason: str | None = None,
) -> Correction:
    """Record a correction and capture context snapshot."""
    context = await _build_context_snapshot(db, entity_type, entity_id)

    repo = CorrectionRepository(db)
    correction = await repo.create(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        context_data=context,
    )

    # Also log to audit trail
    await log_action(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action="correction",
        changes={
            "field": field_name,
            "old": old_value,
            "new": new_value,
            "reason": reason,
        },
    )

    logger.info(
        "Correction recorded: %s.%s %s -> %s (by user %s)",
        entity_type,
        field_name,
        old_value,
        new_value,
        user_id,
    )
    return correction


async def get_correction_history(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: str | None = None,
    field_name: str | None = None,
    since: datetime | None = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict], int]:
    """Get correction history with pagination."""
    repo = CorrectionRepository(db)
    offset = (page - 1) * limit
    corrections = await repo.find_by_tenant(
        tenant_id,
        entity_type=entity_type,
        field_name=field_name,
        since=since,
        offset=offset,
        limit=limit,
    )
    total = await repo.count_by_tenant(
        tenant_id, entity_type=entity_type, field_name=field_name
    )

    items = [
        {
            "id": str(c.id),
            "entity_type": c.entity_type,
            "entity_id": str(c.entity_id),
            "field_name": c.field_name,
            "old_value": c.old_value,
            "new_value": c.new_value,
            "reason": c.reason,
            "context_data": c.context_data,
            "created_at": c.created_at.isoformat(),
            "user_id": str(c.user_id),
        }
        for c in corrections
    ]
    return items, total


async def get_entity_corrections(
    db: AsyncSession, entity_type: str, entity_id: uuid.UUID
) -> list[dict]:
    """Get all corrections for a specific entity."""
    repo = CorrectionRepository(db)
    corrections = await repo.find_by_entity(entity_type, entity_id)
    return [
        {
            "id": str(c.id),
            "field_name": c.field_name,
            "old_value": c.old_value,
            "new_value": c.new_value,
            "reason": c.reason,
            "context_data": c.context_data,
            "created_at": c.created_at.isoformat(),
            "user_id": str(c.user_id),
        }
        for c in corrections
    ]


async def get_correction_stats(
    db: AsyncSession, tenant_id: uuid.UUID
) -> dict:
    """Get correction statistics for a tenant."""
    repo = CorrectionRepository(db)
    stats = await repo.get_correction_stats(tenant_id)
    total = await repo.count_by_tenant(tenant_id)

    by_entity_type: dict[str, int] = {}
    for s in stats:
        et = s["entity_type"]
        by_entity_type[et] = by_entity_type.get(et, 0) + s["count"]

    return {
        "total_corrections": total,
        "by_field": stats,
        "by_entity_type": by_entity_type,
    }
