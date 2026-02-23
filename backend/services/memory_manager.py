"""Long-term memory management: stores and retrieves user preferences and correction history."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.memory import CorrectionRepository, PreferenceRepository


async def get_preferences(tenant_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    repo = PreferenceRepository(db)
    prefs = await repo.find_by_tenant(tenant_id)
    return [
        {
            "id": str(p.id),
            "report_type": p.report_type,
            "column_mappings": p.column_mappings,
            "format_rules": p.format_rules,
            "auto_fill_rules": p.auto_fill_rules,
        }
        for p in prefs
    ]


async def get_preference(
    tenant_id: uuid.UUID, report_type: str, db: AsyncSession
) -> dict | None:
    repo = PreferenceRepository(db)
    pref = await repo.get_by_tenant_and_type(tenant_id, report_type)
    if not pref:
        return None
    return {
        "id": str(pref.id),
        "report_type": pref.report_type,
        "column_mappings": pref.column_mappings,
        "format_rules": pref.format_rules,
        "auto_fill_rules": pref.auto_fill_rules,
    }


async def upsert_preference(
    tenant_id: uuid.UUID,
    report_type: str,
    column_mappings: dict | None = None,
    format_rules: dict | None = None,
    auto_fill_rules: dict | None = None,
    db: AsyncSession = None,
) -> dict:
    repo = PreferenceRepository(db)
    pref = await repo.get_by_tenant_and_type(tenant_id, report_type)

    if pref:
        updates = {}
        if column_mappings is not None:
            updates["column_mappings"] = {**pref.column_mappings, **column_mappings}
        if format_rules is not None:
            updates["format_rules"] = {**pref.format_rules, **format_rules}
        if auto_fill_rules is not None:
            updates["auto_fill_rules"] = {**pref.auto_fill_rules, **auto_fill_rules}
        pref = await repo.update(pref, **updates)
    else:
        pref = await repo.create(
            tenant_id=tenant_id,
            report_type=report_type,
            column_mappings=column_mappings or {},
            format_rules=format_rules or {},
            auto_fill_rules=auto_fill_rules or {},
        )

    return {
        "id": str(pref.id),
        "report_type": pref.report_type,
        "column_mappings": pref.column_mappings,
        "format_rules": pref.format_rules,
        "auto_fill_rules": pref.auto_fill_rules,
    }


async def record_correction(
    tenant_id: uuid.UUID,
    report_type: str,
    field_name: str,
    old_value: str,
    new_value: str,
    reason: str | None,
    db: AsyncSession,
) -> None:
    repo = CorrectionRepository(db)
    await repo.create(
        tenant_id=tenant_id,
        report_type=report_type,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
    )


async def delete_preference(tenant_id: uuid.UUID, report_type: str, db: AsyncSession) -> bool:
    repo = PreferenceRepository(db)
    pref = await repo.get_by_tenant_and_type(tenant_id, report_type)
    if not pref:
        return False
    await repo.delete(pref)
    return True
