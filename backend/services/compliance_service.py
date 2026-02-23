"""Compliance validation orchestrator — runs rules + RAG + scoring and persists results."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.correction import ValidationResult
from backend.repositories.report import ReportRepository
from backend.repositories.validation_result_repo import ValidationResultRepository
from backend.services.audit_logger import log_action
from backend.services.compliance_rules import run_all_checks
from backend.services.compliance_scorer import calculate_compliance_score
from backend.services.rag_validator import validate_with_rag

logger = logging.getLogger(__name__)


async def validate_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """Run full compliance validation on a report.

    1. Load report data
    2. Run deterministic rule checks
    3. Run RAG-based validation
    4. Calculate score
    5. Persist result and update report.compliance_score
    """
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(report_id)
    if not report or report.tenant_id != tenant_id:
        raise ValueError("Report not found")

    data = report.calculated_data or {}
    report_type = report.report_type

    # Gather prior period data for period-over-period check
    prior_data = await _get_prior_period_data(db, tenant_id, report_type, report.period)

    # Gather existing reports for duplicate check
    existing_reports = await _get_existing_reports(db, tenant_id, report_type)

    # Step 1: Deterministic rule checks
    check_results = run_all_checks(
        data=data,
        report_type=report_type,
        prior_data=prior_data,
        existing_reports=existing_reports,
    )

    # Step 2: RAG-based validation
    rag_findings = await validate_with_rag(data, report_type, db)

    # Step 3: Calculate score
    score = calculate_compliance_score(check_results, rag_findings)

    # Step 4: Persist
    vr_repo = ValidationResultRepository(db)
    validation = await vr_repo.create(
        report_id=report_id,
        tenant_id=tenant_id,
        overall_score=score,
        check_results=check_results,
        rag_findings=rag_findings or [],
    )

    # Update report compliance_score
    report.compliance_score = score
    await db.flush()

    await log_action(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type="report",
        entity_id=report_id,
        action="compliance_validation",
        changes={"compliance_score": score},
    )

    logger.info("Compliance validation: report %s score=%d", report_id, score)

    return {
        "id": str(validation.id),
        "report_id": str(report_id),
        "overall_score": score,
        "check_results": check_results,
        "rag_findings": rag_findings or [],
        "validated_at": validation.validated_at.isoformat(),
    }


async def get_latest_validation(
    db: AsyncSession, report_id: uuid.UUID
) -> dict | None:
    """Get the most recent validation result for a report."""
    repo = ValidationResultRepository(db)
    result = await repo.find_latest_by_report(report_id)
    if not result:
        return None
    return {
        "id": str(result.id),
        "report_id": str(result.report_id),
        "overall_score": result.overall_score,
        "check_results": result.check_results,
        "rag_findings": result.rag_findings,
        "validated_at": result.validated_at.isoformat(),
    }


async def get_validation_history(
    db: AsyncSession, report_id: uuid.UUID
) -> list[dict]:
    """Get all validation results for a report."""
    repo = ValidationResultRepository(db)
    results = await repo.find_by_report(report_id)
    return [
        {
            "id": str(r.id),
            "overall_score": r.overall_score,
            "check_results": r.check_results,
            "rag_findings": r.rag_findings,
            "validated_at": r.validated_at.isoformat(),
        }
        for r in results
    ]


async def _get_prior_period_data(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    report_type: str,
    current_period: str,
) -> dict | None:
    """Find the previous period's report data for comparison."""
    repo = ReportRepository(db)
    reports = await repo.find_by_tenant(tenant_id, offset=0, limit=50)
    # Find same-type reports sorted by period, get the one before current
    same_type = sorted(
        [r for r in reports if r.report_type == report_type and r.period < current_period],
        key=lambda r: r.period,
        reverse=True,
    )
    if same_type:
        return same_type[0].calculated_data
    return None


async def _get_existing_reports(
    db: AsyncSession, tenant_id: uuid.UUID, report_type: str
) -> list[dict]:
    """Get summary of existing reports for duplicate checking."""
    repo = ReportRepository(db)
    reports = await repo.find_by_tenant(tenant_id, offset=0, limit=100)
    return [
        {
            "report_type": r.report_type,
            "period": r.period,
            "status": r.status,
        }
        for r in reports
        if r.report_type == report_type
    ]
