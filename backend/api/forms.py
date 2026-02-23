from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.tenant import User
from backend.schemas.common import ok
from backend.services.schema_registry import get_form_schema, list_active_schemas

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("")
async def list_forms(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List all active form schemas."""
    schemas = await list_active_schemas(db)
    return ok(schemas)


@router.get("/{form_type}")
async def get_form(
    form_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get full schema for a form type."""
    schema = await get_form_schema(form_type, db)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form schema '{form_type}' not found",
        )
    return ok({
        "form_type": schema.form_type,
        "name": schema.name,
        "frequency": schema.frequency,
        "version": schema.version,
        "schema_def": schema.schema_def,
        "calculation_rules": schema.calculation_rules,
    })
