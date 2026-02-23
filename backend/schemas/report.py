from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    report_type: str = "BIR_2550M"
    period: str  # e.g. "2026-01"
    data_file_id: str | None = None
    column_mappings: dict[str, str] | None = None  # {source_col: target_field}
    manual_data: dict | None = None


class ReportResponse(BaseModel):
    id: str
    report_type: str
    period: str
    status: str
    calculated_data: dict | None
    created_at: str
    confirmed_at: str | None

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int
