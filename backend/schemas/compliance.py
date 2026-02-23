"""Pydantic schemas for compliance validation."""

from pydantic import BaseModel


class ValidationResponse(BaseModel):
    id: str
    report_id: str
    overall_score: int
    check_results: list[dict]
    rag_findings: list[dict]
    validated_at: str
