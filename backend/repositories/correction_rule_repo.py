"""Repository for learned correction rules."""

import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.correction import CorrectionRule
from backend.repositories.base import BaseRepository


class CorrectionRuleRepository(BaseRepository[CorrectionRule]):
    def __init__(self, session: AsyncSession):
        super().__init__(CorrectionRule, session)

    async def find_active(self, tenant_id: uuid.UUID) -> list[CorrectionRule]:
        query = (
            select(CorrectionRule)
            .where(
                and_(
                    CorrectionRule.tenant_id == tenant_id,
                    CorrectionRule.is_active == True,
                )
            )
            .order_by(CorrectionRule.confidence.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[CorrectionRule]:
        query = (
            select(CorrectionRule)
            .where(CorrectionRule.tenant_id == tenant_id)
            .order_by(CorrectionRule.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert(
        self,
        tenant_id: uuid.UUID,
        rule_type: str,
        match_criteria: dict,
        correction_field: str,
        correction_value: str,
        source_correction_count: int,
        confidence: float = 0.85,
    ) -> CorrectionRule:
        """Create or update a rule matching the same criteria+field+value."""
        query = select(CorrectionRule).where(
            and_(
                CorrectionRule.tenant_id == tenant_id,
                CorrectionRule.correction_field == correction_field,
                CorrectionRule.correction_value == correction_value,
                CorrectionRule.rule_type == rule_type,
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.match_criteria = match_criteria
            existing.source_correction_count = source_correction_count
            existing.confidence = confidence
            await self.session.flush()
            return existing

        return await self.create(
            tenant_id=tenant_id,
            rule_type=rule_type,
            match_criteria=match_criteria,
            correction_field=correction_field,
            correction_value=correction_value,
            source_correction_count=source_correction_count,
            confidence=confidence,
        )

    async def deactivate(self, rule_id: uuid.UUID) -> CorrectionRule | None:
        rule = await self.get_by_id(rule_id)
        if rule:
            rule.is_active = False
            await self.session.flush()
        return rule

    async def activate(self, rule_id: uuid.UUID) -> CorrectionRule | None:
        rule = await self.get_by_id(rule_id)
        if rule:
            rule.is_active = True
            await self.session.flush()
        return rule
