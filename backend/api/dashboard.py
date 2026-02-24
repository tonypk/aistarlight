from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.bank_recon import BankReconciliationBatch
from backend.models.receipt import ReceiptBatch
from backend.models.reconciliation import ReconciliationSession
from backend.models.report import Report
from backend.models.tenant import User
from backend.schemas.common import ok, fail

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get dashboard statistics for the current tenant."""
    tid = user.tenant_id

    # Report counts by status
    report_rows = (
        await db.execute(
            select(Report.status, func.count())
            .where(Report.tenant_id == tid)
            .group_by(Report.status)
        )
    ).all()
    reports_by_status = {row[0]: row[1] for row in report_rows}
    total_reports = sum(reports_by_status.values())

    # Latest compliance score
    latest_report = (
        await db.execute(
            select(Report.compliance_score)
            .where(Report.tenant_id == tid, Report.compliance_score.isnot(None))
            .order_by(Report.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # Reconciliation session count
    session_count = (
        await db.execute(
            select(func.count())
            .select_from(ReconciliationSession)
            .where(ReconciliationSession.tenant_id == tid)
        )
    ).scalar() or 0

    # Bank recon batch count
    bank_recon_count = (
        await db.execute(
            select(func.count())
            .select_from(BankReconciliationBatch)
            .where(BankReconciliationBatch.tenant_id == tid)
        )
    ).scalar() or 0

    # Receipt batch count
    receipt_count = (
        await db.execute(
            select(func.count())
            .select_from(ReceiptBatch)
            .where(ReceiptBatch.tenant_id == tid)
        )
    ).scalar() or 0

    # Knowledge chunk count
    knowledge_count = (
        await db.execute(text("SELECT COUNT(*) FROM knowledge_chunks"))
    ).scalar() or 0

    return ok({
        "total_reports": total_reports,
        "reports_by_status": reports_by_status,
        "compliance_score": float(latest_report) if latest_report else None,
        "session_count": session_count,
        "bank_recon_count": bank_recon_count,
        "receipt_count": receipt_count,
        "knowledge_count": knowledge_count,
    })


@router.get("/calendar")
async def get_filing_calendar(
    year: int = Query(default=0),
    months_ahead: int = Query(default=3, ge=1, le=12),
    _user: User = Depends(get_current_user),
):
    """Get BIR filing calendar with upcoming deadlines."""
    from backend.services.filing_calendar import generate_filing_calendar

    if year == 0:
        year = date.today().year
    events = generate_filing_calendar(year=year, months_ahead=months_ahead)
    return ok(events)


@router.get("/compare")
async def compare_periods(
    period_a: str = Query(..., description="First period (e.g., 2026-01)"),
    period_b: str = Query(..., description="Second period (e.g., 2026-02)"),
    report_type: str = Query(default="BIR_2550M"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Compare report data between two periods."""
    tid = user.tenant_id

    report_a = (
        await db.execute(
            select(Report)
            .where(Report.tenant_id == tid, Report.period == period_a, Report.report_type == report_type)
            .order_by(Report.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    report_b = (
        await db.execute(
            select(Report)
            .where(Report.tenant_id == tid, Report.period == period_b, Report.report_type == report_type)
            .order_by(Report.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if not report_a and not report_b:
        return fail("No reports found for either period")

    def extract_data(report: Report | None) -> dict:
        if not report:
            return {}
        data = report.data or {}
        # Merge overrides
        if report.field_overrides:
            data = {**data, **report.field_overrides}
        return data

    data_a = extract_data(report_a)
    data_b = extract_data(report_b)

    # Calculate differences for numeric fields
    all_keys = sorted(set(list(data_a.keys()) + list(data_b.keys())))
    comparison = []
    for key in all_keys:
        val_a = data_a.get(key)
        val_b = data_b.get(key)
        try:
            num_a = float(val_a) if val_a is not None else None
            num_b = float(val_b) if val_b is not None else None
            diff = None
            pct_change = None
            if num_a is not None and num_b is not None:
                diff = num_b - num_a
                if num_a != 0:
                    pct_change = round((diff / abs(num_a)) * 100, 2)
            comparison.append({
                "field": key,
                "period_a": num_a,
                "period_b": num_b,
                "diff": diff,
                "pct_change": pct_change,
            })
        except (ValueError, TypeError):
            # Skip non-numeric fields
            pass

    return ok({
        "period_a": period_a,
        "period_b": period_b,
        "report_type": report_type,
        "has_report_a": report_a is not None,
        "has_report_b": report_b is not None,
        "comparison": comparison,
    })
