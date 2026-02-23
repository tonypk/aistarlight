"""Pydantic schemas for correction tracking."""

from pydantic import BaseModel


class CorrectionCreate(BaseModel):
    entity_type: str  # transaction_classification / report_field / ewt_classification
    entity_id: str
    field_name: str
    old_value: str | None = None
    new_value: str
    reason: str | None = None


class CorrectionResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    field_name: str
    old_value: str | None
    new_value: str
    reason: str | None
    context_data: dict | None
    created_at: str
    user_id: str


class CorrectionStats(BaseModel):
    total_corrections: int
    by_field: list[dict]
    by_entity_type: dict[str, int]
