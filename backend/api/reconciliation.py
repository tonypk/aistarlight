"""Reconciliation API endpoints."""

import csv
import io
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_tenant, get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.repositories.anomaly_repo import AnomalyRepository
from backend.repositories.reconciliation_repo import ReconciliationSessionRepository
from backend.repositories.report import ReportRepository
from backend.repositories.transaction import TransactionRepository
from backend.schemas.common import fail, ok
from backend.schemas.reconciliation import (
    AnomalyResolveRequest,
    ClassifyRequest,
    FileAddRequest,
    ReconcileRequest,
    SessionCreateRequest,
    TransactionUpdateRequest,
)
from backend.services.anomaly_detector import run_anomaly_detection
from backend.services.audit_logger import log_action
from backend.services.bank_parser import auto_detect_and_parse
from backend.services.classifier_service import classify_transactions
from backend.services.data_processor import apply_column_mapping, extract_full_data
from backend.services.file_utils import find_uploaded_file
from backend.services.reconciliation_engine import (
    generate_vat_summary,
    reconcile,
)

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


# ---- Helpers ----

def _session_response(session) -> dict:
    return {
        "id": str(session.id),
        "period": session.period,
        "status": session.status,
        "report_id": str(session.report_id) if session.report_id else None,
        "source_files": session.source_files or [],
        "summary": session.summary,
        "reconciliation_result": session.reconciliation_result,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


def _txn_response(txn) -> dict:
    return {
        "id": str(txn.id),
        "source_type": txn.source_type,
        "source_file_id": txn.source_file_id,
        "row_index": txn.row_index,
        "date": txn.date.isoformat() if txn.date else None,
        "description": txn.description,
        "amount": float(txn.amount),
        "vat_amount": float(txn.vat_amount),
        "vat_type": txn.vat_type,
        "category": txn.category,
        "tin": txn.tin,
        "confidence": float(txn.confidence),
        "classification_source": txn.classification_source,
        "match_group_id": str(txn.match_group_id) if txn.match_group_id else None,
        "match_status": txn.match_status,
        "ewt_rate": float(txn.ewt_rate) if txn.ewt_rate is not None else None,
        "ewt_amount": float(txn.ewt_amount) if txn.ewt_amount is not None else None,
        "atc_code": txn.atc_code,
        "supplier_id": str(txn.supplier_id) if txn.supplier_id else None,
    }


def _anomaly_response(anomaly) -> dict:
    return {
        "id": str(anomaly.id),
        "transaction_id": str(anomaly.transaction_id) if anomaly.transaction_id else None,
        "anomaly_type": anomaly.anomaly_type,
        "severity": anomaly.severity,
        "description": anomaly.description,
        "details": anomaly.details,
        "status": anomaly.status,
        "resolved_by": str(anomaly.resolved_by) if anomaly.resolved_by else None,
        "resolved_at": anomaly.resolved_at.isoformat() if anomaly.resolved_at else None,
        "resolution_note": anomaly.resolution_note,
        "created_at": anomaly.created_at.isoformat(),
    }


# ---- Session CRUD ----

@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Create a new reconciliation session."""
    repo = ReconciliationSessionRepository(db)
    session = await repo.create(
        tenant_id=user.tenant_id,
        created_by=user.id,
        period=data.period,
        status="draft",
        report_id=data.report_id,
        source_files=[],
    )
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="reconciliation_session", entity_id=session.id,
        action="create", changes={"period": data.period},
    )
    return ok(_session_response(session))


@router.get("/sessions")
async def list_sessions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List reconciliation sessions (paginated)."""
    repo = ReconciliationSessionRepository(db)
    offset = (page - 1) * limit
    sessions = await repo.find_by_tenant(user.tenant_id, offset=offset, limit=limit)
    total = await repo.count(tenant_id=user.tenant_id)
    return ok(
        [_session_response(s) for s in sessions],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get session details."""
    repo = ReconciliationSessionRepository(db)
    session = await repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return ok(_session_response(session))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Delete a session (only if draft)."""
    repo = ReconciliationSessionRepository(db)
    session = await repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "draft":
        raise HTTPException(status_code=409, detail="Can only delete draft sessions")
    await repo.delete(session)
    return ok({"deleted": True})


# ---- Files & Transactions ----

@router.post("/sessions/{session_id}/files")
async def add_file(
    session_id: str,
    data: FileAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Add a file to the session: parse, import transactions."""
    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    filepath, filename = find_uploaded_file(data.file_id)
    with open(filepath, "rb") as f:
        file_content = f.read()

    txn_repo = TransactionRepository(db)

    if data.source_type == "bank_statement":
        # Bank statement: auto-detect format and parse
        parsed = await auto_detect_and_parse(file_content, filename, data.sheet_name)
        raw_rows = parsed["transactions"]
        transactions_to_insert = []
        for i, row in enumerate(raw_rows):
            transactions_to_insert.append({
                "tenant_id": user.tenant_id,
                "session_id": session.id,
                "source_type": "bank_statement",
                "source_file_id": data.file_id,
                "row_index": i,
                "date": _parse_date_safe(row.get("date")),
                "description": row.get("description"),
                "amount": row.get("amount", 0),
                "vat_amount": 0,
                "vat_type": "vatable",
                "category": "goods",
                "confidence": 0,
                "classification_source": "ai",
                "raw_data": row,
            })
        file_info = {
            "file_id": data.file_id,
            "filename": filename,
            "file_type": "bank_statement",
            "sheet_name": data.sheet_name,
            "row_count": len(raw_rows),
            "bank_name": parsed.get("bank_name"),
        }
    else:
        # Sales/purchase records: use column mapping
        rows = extract_full_data(file_content, filename, sheet_name=data.sheet_name)
        if data.column_mappings:
            sales_data, purchases_data = apply_column_mapping(rows, data.column_mappings)
            mapped_rows = (
                [{"_source": "sales", **r} for r in sales_data]
                + [{"_source": "purchases", **r} for r in purchases_data]
            )
        else:
            mapped_rows = [{"_source": data.source_type, **r} for r in rows]

        transactions_to_insert = []
        for i, row in enumerate(mapped_rows):
            source = data.source_type
            if row.get("_source") == "sales":
                source = "sales_record"
            elif row.get("_source") == "purchases":
                source = "purchase_record"
            transactions_to_insert.append({
                "tenant_id": user.tenant_id,
                "session_id": session.id,
                "source_type": source,
                "source_file_id": data.file_id,
                "row_index": i,
                "date": _parse_date_safe(row.get("date")),
                "description": row.get("description"),
                "amount": float(row.get("amount", 0)),
                "vat_amount": float(row.get("vat_amount", 0)),
                "vat_type": row.get("vat_type", "vatable"),
                "category": row.get("category", "goods"),
                "tin": row.get("tin"),
                "confidence": 0,
                "classification_source": "ai",
                "raw_data": {k: v for k, v in row.items() if k != "_source"},
            })
        file_info = {
            "file_id": data.file_id,
            "filename": filename,
            "file_type": data.source_type,
            "sheet_name": data.sheet_name,
            "row_count": len(transactions_to_insert),
        }

    inserted = await txn_repo.bulk_create(transactions_to_insert)

    # Update session source_files
    new_files = list(session.source_files or []) + [file_info]
    await sess_repo.update(session, source_files=new_files)

    return ok({
        "file": file_info,
        "transactions_imported": len(inserted),
    })


@router.post("/sessions/{session_id}/classify")
async def classify_session_transactions(
    session_id: str,
    data: ClassifyRequest = ClassifyRequest(),
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Trigger AI classification on all session transactions."""
    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    txn_repo = TransactionRepository(db)
    transactions = await txn_repo.find_all_by_session(session.id)
    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions to classify")

    # Skip already classified unless force
    to_classify = transactions
    if not data.force:
        to_classify = [t for t in transactions if t.classification_source == "ai" and float(t.confidence) == 0]
        if not to_classify:
            return ok({"message": "All transactions already classified", "count": 0})

    # Build input for classifier
    txn_dicts = [
        {
            "date": t.date.isoformat() if t.date else None,
            "description": t.description,
            "amount": float(t.amount),
            "tin": t.tin,
        }
        for t in to_classify
    ]

    tenant_context = {
        "vat_classification": tenant.vat_classification,
    }

    await sess_repo.update(session, status="classifying")

    # Classify
    results = await classify_transactions(txn_dicts, tenant_context)

    # Update transactions with classification results
    classified_count = 0
    for txn, result in zip(to_classify, results):
        await txn_repo.update(
            txn,
            vat_type=result.get("vat_type", "vatable"),
            category=result.get("category", "goods"),
            confidence=result.get("confidence", 0),
            classification_source=result.get("classification_source", "ai"),
        )
        classified_count += 1

    await sess_repo.update(session, status="reviewing")

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="reconciliation_session", entity_id=session.id,
        action="classify",
        changes={"classified": classified_count, "total": len(transactions)},
    )

    return ok({"classified": classified_count, "total": len(transactions)})


@router.get("/sessions/{session_id}/transactions")
async def list_transactions(
    session_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    vat_type: str | None = None,
    category: str | None = None,
    source_type: str | None = None,
    match_status: str | None = None,
    min_confidence: float | None = None,
    search: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List transactions for a session (paginated + filtered)."""
    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    filters = {
        "vat_type": vat_type,
        "category": category,
        "source_type": source_type,
        "match_status": match_status,
        "min_confidence": min_confidence,
        "search": search,
    }
    offset = (page - 1) * limit
    txn_repo = TransactionRepository(db)
    transactions = await txn_repo.find_by_session(session.id, offset=offset, limit=limit, filters=filters)
    total = await txn_repo.count_by_session(session.id, filters=filters)

    return ok(
        [_txn_response(t) for t in transactions],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.patch("/sessions/{session_id}/transactions/{txn_id}")
async def update_transaction(
    session_id: str,
    txn_id: str,
    data: TransactionUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Override a transaction's classification."""
    txn_repo = TransactionRepository(db)
    txn = await txn_repo.get_by_id(uuid.UUID(txn_id))
    if not txn or txn.tenant_id != user.tenant_id or str(txn.session_id) != session_id:
        raise HTTPException(status_code=404, detail="Transaction not found")

    updates = {}
    if data.vat_type is not None:
        updates["vat_type"] = data.vat_type
    if data.category is not None:
        updates["category"] = data.category
    if data.tin is not None:
        updates["tin"] = data.tin
    if updates:
        updates["classification_source"] = "user_override"
        updates["confidence"] = 1.0
        txn = await txn_repo.update(txn, **updates)

    return ok(_txn_response(txn))


# ---- Anomalies ----

@router.post("/sessions/{session_id}/detect-anomalies")
async def detect_anomalies(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Run anomaly detection on session transactions."""
    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    txn_repo = TransactionRepository(db)
    all_txns = await txn_repo.find_all_by_session(session.id)
    if not all_txns:
        raise HTTPException(status_code=400, detail="No transactions to analyze")

    txn_dicts = [_txn_response(t) for t in all_txns]
    bank_txns = [t for t in txn_dicts if t["source_type"] == "bank_statement"]
    record_txns = [t for t in txn_dicts if t["source_type"] != "bank_statement"]

    detected = await run_anomaly_detection(
        session_id=session.id,
        transactions=txn_dicts,
        bank_transactions=bank_txns if bank_txns else None,
    )

    # Clear previous anomalies and insert new ones
    anomaly_repo = AnomalyRepository(db)
    await anomaly_repo.delete_by_session(session.id)

    anomaly_records = [
        {
            "tenant_id": user.tenant_id,
            "session_id": session.id,
            "transaction_id": uuid.UUID(a.transaction_id) if a.transaction_id else None,
            "anomaly_type": a.anomaly_type,
            "severity": a.severity,
            "description": a.description,
            "details": a.details,
            "status": "open",
        }
        for a in detected
    ]
    if anomaly_records:
        await anomaly_repo.bulk_create(anomaly_records)

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="reconciliation_session", entity_id=session.id,
        action="detect_anomalies",
        changes={"anomalies_found": len(detected)},
    )

    return ok({"anomalies_found": len(detected)})


@router.get("/sessions/{session_id}/anomalies")
async def list_anomalies(
    session_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List anomalies for a session."""
    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    offset = (page - 1) * limit
    anomaly_repo = AnomalyRepository(db)
    anomalies = await anomaly_repo.find_by_session(session.id, offset=offset, limit=limit, status_filter=status_filter)
    total = await anomaly_repo.count_by_session(session.id, status_filter=status_filter)

    return ok(
        [_anomaly_response(a) for a in anomalies],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.patch("/sessions/{session_id}/anomalies/{anomaly_id}")
async def resolve_anomaly(
    session_id: str,
    anomaly_id: str,
    data: AnomalyResolveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Resolve/acknowledge an anomaly."""
    anomaly_repo = AnomalyRepository(db)
    anomaly = await anomaly_repo.get_by_id(uuid.UUID(anomaly_id))
    if not anomaly or anomaly.tenant_id != user.tenant_id or str(anomaly.session_id) != session_id:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    await anomaly_repo.update(
        anomaly,
        status=data.status,
        resolved_by=user.id,
        resolved_at=datetime.now(UTC),
        resolution_note=data.resolution_note,
    )

    return ok(_anomaly_response(anomaly))


# ---- Summary & Reconciliation ----

@router.get("/sessions/{session_id}/summary")
async def get_vat_summary(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get VAT summary for a session."""
    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    txn_repo = TransactionRepository(db)
    all_txns = await txn_repo.find_all_by_session(session.id)
    txn_dicts = [_txn_response(t) for t in all_txns]

    summary = generate_vat_summary(txn_dicts, session.period)

    # Cache summary on session
    await sess_repo.update(session, summary=summary.to_dict())

    return ok(summary.to_dict())


@router.post("/sessions/{session_id}/reconcile")
async def run_reconciliation(
    session_id: str,
    data: ReconcileRequest = ReconcileRequest(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Run full reconciliation: match + summarize + compare with declared report."""
    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    txn_repo = TransactionRepository(db)
    all_txns = await txn_repo.find_all_by_session(session.id)
    if not all_txns:
        raise HTTPException(status_code=400, detail="No transactions to reconcile")

    txn_dicts = [_txn_response(t) for t in all_txns]
    sales = [t for t in txn_dicts if t["source_type"] == "sales_record"]
    purchases = [t for t in txn_dicts if t["source_type"] == "purchase_record"]
    bank = [t for t in txn_dicts if t["source_type"] == "bank_statement"]

    # Fetch declared report for comparison
    declared_report = None
    report_id = data.report_id or session.report_id
    if report_id:
        report_repo = ReportRepository(db)
        report = await report_repo.get_by_id(report_id)
        if report and report.tenant_id == user.tenant_id:
            declared_report = {
                "id": str(report.id),
                "calculated_data": report.calculated_data,
            }

    # Count anomalies
    anomaly_repo = AnomalyRepository(db)
    anomaly_count = await anomaly_repo.count_by_session(session.id)

    result = await reconcile(
        session_id=session.id,
        sales=sales,
        purchases=purchases,
        bank=bank if bank else None,
        declared_report=declared_report,
        period=session.period,
        amount_tolerance=data.amount_tolerance,
        date_tolerance_days=data.date_tolerance_days,
    )
    result["anomaly_count"] = anomaly_count

    # Update match statuses on transactions
    if result.get("match_stats", {}).get("pairs"):
        for pair in result["match_stats"]["pairs"]:
            match_group_id = uuid.UUID(pair["match_group_id"])
            for id_key in ("record_id", "bank_id"):
                txn_id = pair.get(id_key)
                if txn_id:
                    txn = await txn_repo.get_by_id(uuid.UUID(txn_id))
                    if txn:
                        await txn_repo.update(txn, match_group_id=match_group_id, match_status="matched")

    # Cache result and update status
    await sess_repo.update(
        session,
        reconciliation_result=result,
        summary=result.get("summary"),
        status="completed",
        completed_at=datetime.now(UTC),
    )

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="reconciliation_session", entity_id=session.id,
        action="reconcile",
        changes={"match_rate": result.get("match_stats", {}).get("match_rate", 0)},
    )

    return ok(result)


# ---- Report Generation ----

@router.post("/sessions/{session_id}/generate-report")
async def generate_report_from_session(
    session_id: str,
    report_type: str = "BIR_2550M",
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Generate a BIR report directly from reconciliation session data."""
    from backend.repositories.report import ReportRepository
    from backend.services.report_generator import generate_pdf_report
    from backend.services.tax_engine import calculate_report

    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    txn_repo = TransactionRepository(db)
    all_txns = await txn_repo.find_all_by_session(session.id)
    if not all_txns:
        raise HTTPException(status_code=400, detail="Session has no transactions")

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

    calculated = await calculate_report(
        form_type=report_type,
        sales_data=sales_data,
        purchases_data=purchases_data,
        db=db,
    )
    calculated["period"] = session.period

    tenant_info = {
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
    }
    file_path = generate_pdf_report(report_type, calculated, tenant_info)

    report_repo = ReportRepository(db)
    report = await report_repo.create(
        tenant_id=tenant.id,
        report_type=report_type,
        period=session.period,
        status="draft",
        input_data={"session_id": session_id, "sales_count": len(sales_data), "purchases_count": len(purchases_data)},
        calculated_data=calculated,
        file_path=file_path,
        created_by=user.id,
    )

    await log_action(
        db, tenant_id=tenant.id, user_id=user.id,
        entity_type="report", entity_id=report.id,
        action="create",
        changes={"report_type": report_type, "period": session.period, "source": "reconciliation"},
    )

    return ok({
        "id": str(report.id),
        "report_type": report.report_type,
        "period": report.period,
        "status": report.status,
    })


# ---- Export ----

@router.get("/sessions/{session_id}/export-pdf")
async def export_reconciliation_pdf(
    session_id: str,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Export reconciliation results as a professional PDF report."""
    from fastapi.responses import FileResponse

    from backend.services.report_generator import generate_reconciliation_pdf

    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = session.summary
    if not summary:
        raise HTTPException(status_code=400, detail="No summary available — run reconciliation first")

    # Fetch anomalies
    anomaly_repo = AnomalyRepository(db)
    anomalies_raw = await anomaly_repo.find_by_session(session.id, offset=0, limit=100)
    anomalies = [_anomaly_response(a) for a in anomalies_raw]

    tenant_info = {
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
    }

    session_data = _session_response(session)
    filepath = generate_reconciliation_pdf(session_data, summary, anomalies, tenant_info)

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="reconciliation_session", entity_id=session.id,
        action="export_pdf",
    )

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=f"reconciliation_{session.period}.pdf",
    )


@router.get("/sessions/{session_id}/export")
async def export_transactions(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Export session transactions as CSV."""
    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    txn_repo = TransactionRepository(db)
    transactions = await txn_repo.find_all_by_session(session.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Description", "Amount", "VAT Amount", "VAT Type",
        "Category", "TIN", "Confidence", "Source", "Match Status",
    ])
    for t in transactions:
        writer.writerow([
            t.date.isoformat() if t.date else "",
            t.description or "",
            float(t.amount),
            float(t.vat_amount),
            t.vat_type,
            t.category,
            t.tin or "",
            float(t.confidence),
            t.classification_source,
            t.match_status,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reconciliation_{session.period}.csv"},
    )


# ---- Utility ----

def _parse_date_safe(date_str) -> str | None:
    """Parse date string safely, return date object or None."""
    if date_str is None:
        return None
    if isinstance(date_str, str) and len(date_str) >= 10:
        try:
            from datetime import date as d
            parts = date_str[:10].split("-")
            return d(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            return None
    return None
