"""Pydantic schemas for reconciliation endpoints."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request schemas ---

class SessionCreateRequest(BaseModel):
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$", examples=["2026-01"])
    report_id: UUID | None = None


class FileAddRequest(BaseModel):
    file_id: str
    source_type: str = Field(..., pattern=r"^(sales_record|purchase_record|bank_statement)$")
    sheet_name: str | None = None
    column_mappings: dict[str, str] | None = None


class ClassifyRequest(BaseModel):
    force: bool = False


class TransactionUpdateRequest(BaseModel):
    vat_type: str | None = None
    category: str | None = None
    tin: str | None = None


class AnomalyResolveRequest(BaseModel):
    status: str = Field(..., pattern=r"^(acknowledged|resolved|false_positive)$")
    resolution_note: str | None = None


class ReconcileRequest(BaseModel):
    report_id: UUID | None = None
    amount_tolerance: float = 0.01
    date_tolerance_days: int = 3


# --- Response schemas ---

class SourceFileInfo(BaseModel):
    file_id: str
    filename: str
    file_type: str
    sheet_name: str | None = None
    row_count: int = 0

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: UUID
    period: str
    status: str
    report_id: UUID | None = None
    source_files: list[SourceFileInfo] = []
    summary: dict | None = None
    reconciliation_result: dict | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


class TransactionResponse(BaseModel):
    id: UUID
    source_type: str
    source_file_id: str
    row_index: int
    date: date | None = None
    description: str | None = None
    amount: float
    vat_amount: float = 0
    vat_type: str = "vatable"
    category: str = "goods"
    tin: str | None = None
    confidence: float = 0
    classification_source: str = "ai"
    match_group_id: UUID | None = None
    match_status: str = "unmatched"

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int


class AnomalyResponse(BaseModel):
    id: UUID
    transaction_id: UUID | None = None
    anomaly_type: str
    severity: str
    description: str
    details: dict | None = None
    status: str = "open"
    resolved_by: UUID | None = None
    resolved_at: datetime | None = None
    resolution_note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnomalyListResponse(BaseModel):
    anomalies: list[AnomalyResponse]
    total: int


class VatSummaryResponse(BaseModel):
    period: str
    output_vat: dict
    input_vat: dict
    total_output_vat: float
    total_input_vat: float
    net_vat: float
    transaction_count: int
    classification_stats: dict


class ReconciliationResultResponse(BaseModel):
    period: str
    summary: dict
    comparison: dict | None = None
    match_stats: dict
    anomaly_count: int
