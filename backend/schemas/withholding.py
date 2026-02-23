"""Pydantic schemas for withholding tax feature."""

from pydantic import BaseModel


class SupplierCreateRequest(BaseModel):
    tin: str
    name: str
    address: str | None = None
    supplier_type: str = "corporation"
    default_ewt_rate: float | None = None
    default_atc_code: str | None = None
    is_vat_registered: bool = True


class SupplierUpdateRequest(BaseModel):
    tin: str | None = None
    name: str | None = None
    address: str | None = None
    supplier_type: str | None = None
    default_ewt_rate: float | None = None
    default_atc_code: str | None = None
    is_vat_registered: bool | None = None


class SupplierResponse(BaseModel):
    id: str
    tin: str
    name: str
    address: str | None
    supplier_type: str
    default_ewt_rate: float | None
    default_atc_code: str | None
    is_vat_registered: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CertificateResponse(BaseModel):
    id: str
    supplier_id: str
    supplier_name: str | None = None
    session_id: str | None
    period: str
    quarter: str
    atc_code: str
    income_type: str
    income_amount: float
    ewt_rate: float
    tax_withheld: float
    status: str
    file_path: str | None
    created_at: str

    model_config = {"from_attributes": True}


class EwtSummaryResponse(BaseModel):
    period: str
    total_certificates: int
    total_income: float
    total_tax_withheld: float

    model_config = {"from_attributes": True}
