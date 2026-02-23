from pydantic import BaseModel


class CompanySettingsUpdate(BaseModel):
    company_name: str | None = None
    tin_number: str | None = None
    rdo_code: str | None = None
    vat_classification: str | None = None


class CompanySettingsResponse(BaseModel):
    id: str
    company_name: str
    tin_number: str | None
    rdo_code: str | None
    vat_classification: str
    plan: str

    model_config = {"from_attributes": True}
