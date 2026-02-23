from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    report_type: str = "BIR_2550M"
    period: str  # e.g. "2026-01"
    data_file_id: str | None = None
    column_mappings: dict[str, str] | None = None  # {source_col: target_field}
    sheet_name: str | None = None  # Excel sheet name, defaults to first sheet
    manual_data: dict | None = None


class ReportEditRequest(BaseModel):
    field_overrides: dict[str, str]
    recalculate: bool = True
    notes: str | None = None
    version: int  # optimistic lock — must match current report version


class ReportTransitionRequest(BaseModel):
    target_status: str
    comment: str | None = None


class ReportResponse(BaseModel):
    id: str
    report_type: str
    period: str
    status: str
    calculated_data: dict | None
    created_at: str
    confirmed_at: str | None
    version: int = 1
    overrides: dict | None = None
    original_calculated_data: dict | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int
