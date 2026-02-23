from pydantic import BaseModel


class PreferenceUpdate(BaseModel):
    column_mappings: dict | None = None
    format_rules: dict | None = None
    auto_fill_rules: dict | None = None


class PreferenceResponse(BaseModel):
    id: str
    report_type: str
    column_mappings: dict
    format_rules: dict
    auto_fill_rules: dict

    model_config = {"from_attributes": True}


class CorrectionResponse(BaseModel):
    id: str
    report_type: str
    field_name: str | None
    old_value: str | None
    new_value: str | None
    reason: str | None
    created_at: str

    model_config = {"from_attributes": True}
