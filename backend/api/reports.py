import os
import pathlib
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.deps import get_current_tenant, get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.repositories.report import ReportRepository
from backend.schemas.common import ok
from backend.schemas.report import ReportGenerateRequest
from backend.services.data_processor import apply_column_mapping, extract_full_data
from backend.services.report_generator import generate_pdf_report
from backend.services.tax_engine import calculate_bir_2550m, get_supported_forms

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/supported-forms")
async def list_supported_forms():
    """List all supported BIR form types."""
    return ok(get_supported_forms())


def _find_uploaded_file(file_id: str) -> tuple[str, str]:
    """Find an uploaded file by ID, returns (filepath, filename)."""
    # Validate file_id is a safe UUID-like string
    if not file_id.replace("-", "").isalnum():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file ID")

    upload_root = pathlib.Path(settings.upload_dir).resolve()
    for ext in ("csv", "xlsx", "xls"):
        filepath = (upload_root / f"{file_id}.{ext}").resolve()
        # Ensure path is still inside upload directory
        if not str(filepath).startswith(str(upload_root)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file ID")
        if filepath.exists():
            return str(filepath), f"{file_id}.{ext}"

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Uploaded file {file_id} not found",
    )


@router.post("/generate")
async def generate_report(
    data: ReportGenerateRequest,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Generate a BIR tax report."""
    if data.report_type != "BIR_2550M":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report type {data.report_type} not yet supported",
        )

    input_data = {}

    if data.data_file_id and data.column_mappings:
        # File-based flow: read file → apply mapping → calculate
        filepath, filename = _find_uploaded_file(data.data_file_id)
        with open(filepath, "rb") as f:
            file_content = f.read()

        rows = extract_full_data(file_content, filename, sheet_name=data.sheet_name)
        sales_data, purchases_data = apply_column_mapping(rows, data.column_mappings)
        input_data = {
            "data_file_id": data.data_file_id,
            "column_mappings": data.column_mappings,
            "sales_count": len(sales_data),
            "purchases_count": len(purchases_data),
        }
    elif data.manual_data:
        # Manual data flow
        sales_data = data.manual_data.get("sales_data", [])
        purchases_data = data.manual_data.get("purchases_data", [])
        input_data = data.manual_data
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide data_file_id with column_mappings, or manual_data",
        )

    calculated = calculate_bir_2550m(
        sales_data=sales_data,
        purchases_data=purchases_data,
    )
    calculated["period"] = data.period

    tenant_info = {
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
    }
    file_path = generate_pdf_report(data.report_type, calculated, tenant_info)

    report_repo = ReportRepository(db)
    report = await report_repo.create(
        tenant_id=tenant.id,
        report_type=data.report_type,
        period=data.period,
        status="draft",
        input_data=input_data,
        calculated_data=calculated,
        file_path=file_path,
    )

    return ok({
        "id": str(report.id),
        "report_type": report.report_type,
        "period": report.period,
        "status": report.status,
        "calculated_data": calculated,
    })


@router.get("")
async def list_reports(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List reports for current tenant."""
    report_repo = ReportRepository(db)
    offset = (page - 1) * limit
    reports = await report_repo.find_by_tenant(user.tenant_id, offset=offset, limit=limit)
    total = await report_repo.count(tenant_id=user.tenant_id)
    return ok(
        [
            {
                "id": str(r.id),
                "report_type": r.report_type,
                "period": r.period,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get report details."""
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(uuid.UUID(report_id))
    if not report or report.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ok({
        "id": str(report.id),
        "report_type": report.report_type,
        "period": report.period,
        "status": report.status,
        "calculated_data": report.calculated_data,
        "created_at": report.created_at.isoformat(),
        "confirmed_at": report.confirmed_at.isoformat() if report.confirmed_at else None,
    })


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Download report as PDF."""
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(uuid.UUID(report_id))
    if not report or report.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if not report.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not generated")
    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=f"{report.report_type}_{report.period}.pdf",
    )


@router.patch("/{report_id}/confirm")
async def confirm_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Confirm/finalize a report."""
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(uuid.UUID(report_id))
    if not report or report.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    report = await report_repo.update(report, status="confirmed", confirmed_at=datetime.now(UTC))
    return ok({"id": str(report.id), "status": report.status})
