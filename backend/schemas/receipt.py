"""Pydantic schemas for receipt OCR endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReceiptUploadRequest(BaseModel):
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$", examples=["2026-01"])
    report_type: str = Field(default="BIR_2550M")


class ParsedFieldResponse(BaseModel):
    value: str | float | None = None
    confidence: float = 0.0


class ReceiptParseResult(BaseModel):
    filename: str
    vendor_name: str | None = None
    tin: str | None = None
    date: str | None = None
    total_amount: float | None = None
    vatable_sales: float | None = None
    vat_amount: float | None = None
    vat_type: str = "vatable"
    category: str = "goods"
    receipt_number: str | None = None
    overall_confidence: float = 0.0
    llm_fields_resolved: list[str] = []
    ocr_text: str = ""


class ReceiptBatchResponse(BaseModel):
    id: UUID
    status: str
    total_images: int
    processed_count: int
    session_id: UUID | None = None
    report_id: UUID | None = None
    report_type: str
    period: str
    results: list[dict] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReceiptBatchListResponse(BaseModel):
    batches: list[ReceiptBatchResponse]
    total: int
