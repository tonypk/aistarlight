"""Repository for withholding certificates."""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.withholding import WithholdingCertificate
from backend.repositories.base import BaseRepository


class WithholdingCertificateRepository(BaseRepository[WithholdingCertificate]):
    def __init__(self, session: AsyncSession):
        super().__init__(WithholdingCertificate, session)

    async def find_by_tenant(
        self,
        tenant_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        period: str | None = None,
        supplier_id: uuid.UUID | None = None,
    ) -> list[WithholdingCertificate]:
        query = select(WithholdingCertificate).where(
            WithholdingCertificate.tenant_id == tenant_id
        )
        if period:
            query = query.where(WithholdingCertificate.period == period)
        if supplier_id:
            query = query.where(WithholdingCertificate.supplier_id == supplier_id)
        query = query.order_by(WithholdingCertificate.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_by_session(self, session_id: uuid.UUID) -> list[WithholdingCertificate]:
        result = await self.session.execute(
            select(WithholdingCertificate)
            .where(WithholdingCertificate.session_id == session_id)
            .order_by(WithholdingCertificate.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_tenant(
        self, tenant_id: uuid.UUID, period: str | None = None
    ) -> int:
        query = select(func.count()).select_from(WithholdingCertificate).where(
            WithholdingCertificate.tenant_id == tenant_id
        )
        if period:
            query = query.where(WithholdingCertificate.period == period)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_ewt_summary(
        self, tenant_id: uuid.UUID, period: str
    ) -> dict:
        """Get aggregated EWT summary for a period."""
        result = await self.session.execute(
            select(
                func.count().label("total_certificates"),
                func.sum(WithholdingCertificate.income_amount).label("total_income"),
                func.sum(WithholdingCertificate.tax_withheld).label("total_tax_withheld"),
            )
            .where(
                WithholdingCertificate.tenant_id == tenant_id,
                WithholdingCertificate.period == period,
            )
        )
        row = result.one()
        return {
            "period": period,
            "total_certificates": row.total_certificates,
            "total_income": float(row.total_income or 0),
            "total_tax_withheld": float(row.total_tax_withheld or 0),
        }

    async def bulk_create(self, certificates: list[dict]) -> list[WithholdingCertificate]:
        instances = [WithholdingCertificate(**data) for data in certificates]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    async def delete_by_session(self, session_id: uuid.UUID) -> int:
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(WithholdingCertificate).where(
                WithholdingCertificate.session_id == session_id
            )
        )
        return result.rowcount
