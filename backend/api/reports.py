import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_tenant, get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.models.workflow import is_editable, is_valid_transition
from backend.repositories.report import ReportRepository
from backend.schemas.common import ok
from backend.schemas.report import ReportEditRequest, ReportGenerateRequest, ReportTransitionRequest
from backend.services.audit_logger import log_action
from backend.services.data_processor import apply_column_mapping, extract_full_data
from backend.services.file_utils import find_uploaded_file
from backend.services.report_editor import (
    NotEditableError,
    VersionConflictError,
    apply_field_overrides,
)
from backend.services.report_generator import generate_csv_export, generate_pdf_report
from backend.services.tax_engine import calculate_bir_2550m, calculate_report, get_supported_forms

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/supported-forms")
async def list_supported_forms(
    db: AsyncSession = Depends(get_session),
):
    """List all supported BIR form types (hardcoded + schema-based)."""
    from backend.services.schema_registry import list_active_schemas

    forms = get_supported_forms()
    # Merge in schema-based forms
    try:
        schemas = await list_active_schemas(db)
        for s in schemas:
            if s["form_type"] not in forms:
                forms[s["form_type"]] = {"name": s["name"], "frequency": s["frequency"]}
    except Exception:
        pass  # Schema table may not exist yet
    return ok(forms)


def _find_uploaded_file(file_id: str) -> tuple[str, str]:
    """Find an uploaded file by ID, returns (filepath, filename)."""
    return find_uploaded_file(file_id)


def _report_response(report) -> dict:
    """Build a standard report response dict."""
    return {
        "id": str(report.id),
        "report_type": report.report_type,
        "period": report.period,
        "status": report.status,
        "calculated_data": report.calculated_data,
        "created_at": report.created_at.isoformat(),
        "confirmed_at": report.confirmed_at.isoformat() if report.confirmed_at else None,
        "version": report.version,
        "overrides": report.overrides,
        "original_calculated_data": report.original_calculated_data,
        "notes": report.notes,
        "compliance_score": report.compliance_score,
    }


@router.post("/generate")
async def generate_report(
    data: ReportGenerateRequest,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Generate a BIR tax report."""
    # Check if form type is supported (via schema DB or hardcoded registry)
    from backend.services.schema_registry import get_form_schema

    supported_types = ("BIR_2550M", "BIR_2550Q", "BIR_1601C", "BIR_0619E", "BIR_1701", "BIR_1702", "BIR_2316")
    schema = await get_form_schema(data.report_type, db)
    if not schema and data.report_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report type {data.report_type} not yet supported",
        )

    input_data = {}

    if data.session_id:
        # Auto-fill from reconciliation session transactions
        from backend.repositories.reconciliation_repo import ReconciliationSessionRepository
        from backend.repositories.transaction import TransactionRepository

        sess_repo = ReconciliationSessionRepository(db)
        session = await sess_repo.get_by_id(uuid.UUID(data.session_id))
        if not session or session.tenant_id != tenant.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        txn_repo = TransactionRepository(db)
        all_txns = await txn_repo.find_all_by_session(session.id)
        if not all_txns:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session has no transactions")

        sales_data = [
            {
                "amount": float(t.amount),
                "vat_amount": float(t.vat_amount),
                "vat_type": t.vat_type,
                "category": t.category,
            }
            for t in all_txns
            if t.source_type == "sales_record"
        ]
        purchases_data = [
            {
                "amount": float(t.amount),
                "vat_amount": float(t.vat_amount),
                "vat_type": t.vat_type,
                "category": t.category,
            }
            for t in all_txns
            if t.source_type == "purchase_record"
        ]
        input_data = {
            "session_id": data.session_id,
            "sales_count": len(sales_data),
            "purchases_count": len(purchases_data),
        }
    elif data.data_file_id and data.column_mappings:
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
        sales_data = data.manual_data.get("sales_data", [])
        purchases_data = data.manual_data.get("purchases_data", [])
        input_data = data.manual_data
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide session_id, data_file_id with column_mappings, or manual_data",
        )

    extra_kwargs: dict = {}
    if data.report_type == "BIR_1601C":
        extra_kwargs["compensation_data"] = data.manual_data or {}
    elif data.report_type == "BIR_0619E":
        extra_kwargs["ewt_data"] = data.manual_data or {}
    elif data.report_type in ("BIR_1701", "BIR_1702"):
        extra_kwargs["income_data"] = data.manual_data or {}
    elif data.report_type == "BIR_2316":
        extra_kwargs["compensation_data"] = data.manual_data or {}

    calculated = await calculate_report(
        form_type=data.report_type,
        sales_data=sales_data,
        purchases_data=purchases_data,
        db=db,
        **extra_kwargs,
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
        created_by=user.id,
    )

    await log_action(
        db,
        tenant_id=tenant.id,
        user_id=user.id,
        entity_type="report",
        entity_id=report.id,
        action="create",
        changes={"report_type": data.report_type, "period": data.period},
    )

    return ok(_report_response(report))


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
                "compliance_score": r.compliance_score,
                "created_at": r.created_at.isoformat(),
                "version": r.version,
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
    return ok(_report_response(report))


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

    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        entity_type="report",
        entity_id=report.id,
        action="download",
    )

    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=f"{report.report_type}_{report.period}.pdf",
    )


@router.get("/{report_id}/export-csv")
async def export_report_csv(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Export report data as CSV."""
    import io

    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(uuid.UUID(report_id))
    if not report or report.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if not report.calculated_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No calculated data")

    csv_content = generate_csv_export(report.calculated_data)
    filename = f"{report.report_type}_{report.period}.csv"

    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        entity_type="report",
        entity_id=report.id,
        action="export_csv",
    )

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{report_id}/confirm")
async def confirm_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Confirm/finalize a report. Legacy endpoint — transitions draft → review."""
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(uuid.UUID(report_id))
    if not report or report.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    old_status = report.status
    report = await report_repo.update(report, status="confirmed", confirmed_at=datetime.now(UTC))

    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        entity_type="report",
        entity_id=report.id,
        action="transition",
        changes={"status": {"old": old_status, "new": "confirmed"}},
    )

    return ok({"id": str(report.id), "status": report.status})


@router.patch("/{report_id}/edit")
async def edit_report(
    report_id: str,
    data: ReportEditRequest,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Edit report fields with optional recalculation."""
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(uuid.UUID(report_id))
    if not report or report.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    tenant_info = {
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
    }

    try:
        report = await apply_field_overrides(
            db,
            report=report,
            field_overrides=data.field_overrides,
            recalculate=data.recalculate,
            notes=data.notes,
            expected_version=data.version,
            user_id=user.id,
            tenant_id=user.tenant_id,
            tenant_info=tenant_info,
        )
    except NotEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except VersionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return ok(_report_response(report))


@router.patch("/{report_id}/transition")
async def transition_report(
    report_id: str,
    data: ReportTransitionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Transition report status through the workflow."""
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(uuid.UUID(report_id))
    if not report or report.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if not is_valid_transition(report.status, data.target_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition from '{report.status}' to '{data.target_status}'",
        )

    old_status = report.status
    update_fields: dict = {"status": data.target_status}

    # Set confirmed_at when moving to approved
    if data.target_status == "approved" and not report.confirmed_at:
        update_fields["confirmed_at"] = datetime.now(UTC)

    report = await report_repo.update(report, **update_fields)

    await log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        entity_type="report",
        entity_id=report.id,
        action="transition",
        changes={"status": {"old": old_status, "new": data.target_status}},
        comment=data.comment,
    )

    return ok(_report_response(report))
