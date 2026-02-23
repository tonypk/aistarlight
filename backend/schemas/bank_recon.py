"""Request/response schemas for bank reconciliation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BankReconProcessRequest(BaseModel):
    period: str = Field(..., description="Tax period, e.g. '2026-01'")
    session_id: UUID | None = Field(None, description="Link to existing recon session")
    amount_tolerance: float = Field(0.01, ge=0)
    date_tolerance_days: int = Field(3, ge=0, le=30)
    run_ai_analysis: bool = True


class SourceFileInfo(BaseModel):
    filename: str
    file_type: str
    format_detected: bool
    bank_name: str | None
    row_count: int


class MatchPair(BaseModel):
    match_group_id: str
    record_id: str
    bank_id: str
    record_amount: float
    bank_amount: float
    date_diff_days: int | None = None


class UnmatchedEntry(BaseModel):
    id: str
    amount: float
    date: str | None = None
    description: str | None = None


class MatchResultResponse(BaseModel):
    matched_pairs: list[MatchPair] = []
    unmatched_records: list[UnmatchedEntry] = []
    unmatched_bank: list[UnmatchedEntry] = []
    match_rate: float = 0.0
    total_records: int = 0
    total_bank_entries: int = 0


class AISuggestion(BaseModel):
    unmatched_entry_index: int
    suggested_record_id: str | None = None
    confidence: float
    explanation: str
    category: str
    status: str = "pending"  # pending | accepted | rejected


class AIExplanation(BaseModel):
    entry_index: int
    entry_type: str
    mismatch_type: str
    explanation: str
    recommended_action: str


class BankReconBatchResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    created_by: UUID
    session_id: UUID | None = None
    status: str
    source_files: list[SourceFileInfo] | None = None
    total_entries: int = 0
    parse_summary: dict | None = None
    match_result: MatchResultResponse | None = None
    ai_suggestions: list[AISuggestion] | None = None
    ai_explanations: list[AIExplanation] | None = None
    amount_tolerance: float = 0.01
    date_tolerance_days: int = 3
    period: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BankReconBatchListItem(BaseModel):
    id: UUID
    status: str
    period: str
    total_entries: int = 0
    source_files: list[SourceFileInfo] | None = None
    match_rate: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SuggestionActionRequest(BaseModel):
    suggestion_index: int = Field(..., ge=0)
