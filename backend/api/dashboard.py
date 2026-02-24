from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.bank_recon import BankReconciliationBatch
from backend.models.receipt import ReceiptBatch
from backend.models.reconciliation import ReconciliationSession
from backend.models.report import Report
from backend.models.tenant import User
from backend.schemas.common import ok

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
