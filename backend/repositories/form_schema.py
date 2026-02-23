from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.form_schema import FormSchema
from backend.repositories.base import BaseRepository


class FormSchemaRepository(BaseRepository[FormSchema]):
    def __init__(self, session: AsyncSession):
        super().__init__(FormSchema, session)

    async def get_active(self, form_type: str) -> FormSchema | None:
        result = await self.session.execute(
            select(FormSchema).where(
                FormSchema.form_type == form_type,
                FormSchema.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_active_forms(self) -> list[FormSchema]:
        result = await self.session.execute(
            select(FormSchema)
            .where(FormSchema.is_active.is_(True))
            .order_by(FormSchema.form_type)
        )
        return list(result.scalars().all())
