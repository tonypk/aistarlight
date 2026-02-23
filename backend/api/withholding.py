"""Withholding Tax API endpoints — supplier CRUD, EWT classification, BIR 2307 + SAWT."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_tenant, get_current_user, get_session
from backend.models.tenant import Tenant, User
from backend.repositories.reconciliation_repo import ReconciliationSessionRepository
from backend.repositories.supplier_repo import SupplierRepository
from backend.repositories.transaction import TransactionRepository
from backend.repositories.withholding_repo import WithholdingCertificateRepository
from backend.schemas.common import ok
from backend.schemas.withholding import (
    SupplierCreateRequest,
    SupplierUpdateRequest,
)
from backend.services.audit_logger import log_action

router = APIRouter(prefix="/withholding", tags=["withholding"])


# ---- Helpers ----

def _supplier_response(s) -> dict:
    return {
        "id": str(s.id),
        "tin": s.tin,
        "name": s.name,
        "address": s.address,
        "supplier_type": s.supplier_type,
        "default_ewt_rate": float(s.default_ewt_rate) if s.default_ewt_rate is not None else None,
        "default_atc_code": s.default_atc_code,
        "is_vat_registered": s.is_vat_registered,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


def _certificate_response(cert, supplier_name: str | None = None) -> dict:
    return {
        "id": str(cert.id),
        "supplier_id": str(cert.supplier_id),
        "supplier_name": supplier_name,
        "session_id": str(cert.session_id) if cert.session_id else None,
        "period": cert.period,
        "quarter": cert.quarter,
        "atc_code": cert.atc_code,
        "income_type": cert.income_type,
        "income_amount": float(cert.income_amount),
        "ewt_rate": float(cert.ewt_rate),
        "tax_withheld": float(cert.tax_withheld),
        "status": cert.status,
        "file_path": cert.file_path,
        "created_at": cert.created_at.isoformat(),
    }


def _period_to_quarter(period: str) -> str:
    """Convert period '2026-01' to quarter '2026Q1'."""
    try:
        parts = period.split("-")
        year = parts[0]
        month = int(parts[1])
        q = (month - 1) // 3 + 1
        return f"{year}Q{q}"
    except (IndexError, ValueError):
        return period


# ---- Supplier CRUD ----

@router.get("/suppliers")
async def list_suppliers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    search: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List suppliers for current tenant."""
    repo = SupplierRepository(db)
    if search:
        suppliers = await repo.search(user.tenant_id, search, limit=limit)
        return ok([_supplier_response(s) for s in suppliers])

    offset = (page - 1) * limit
    suppliers = await repo.find_by_tenant(user.tenant_id, offset=offset, limit=limit)
    total = await repo.count(tenant_id=user.tenant_id)
    return ok(
        [_supplier_response(s) for s in suppliers],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Create a new supplier."""
    repo = SupplierRepository(db)

    # Check for duplicate TIN
    existing = await repo.find_by_tin(user.tenant_id, data.tin)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Supplier with TIN {data.tin} already exists",
        )

    supplier = await repo.create(
        tenant_id=user.tenant_id,
        **data.model_dump(),
    )

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="supplier", entity_id=supplier.id,
        action="create", changes={"name": data.name, "tin": data.tin},
    )

    return ok(_supplier_response(supplier))


@router.patch("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    data: SupplierUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Update a supplier."""
    repo = SupplierRepository(db)
    supplier = await repo.get_by_id(uuid.UUID(supplier_id))
    if not supplier or supplier.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Supplier not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        supplier = await repo.update(supplier, **updates)

    return ok(_supplier_response(supplier))


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Delete a supplier."""
    repo = SupplierRepository(db)
    supplier = await repo.get_by_id(uuid.UUID(supplier_id))
    if not supplier or supplier.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Supplier not found")

    await repo.delete(supplier)

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="supplier", entity_id=uuid.UUID(supplier_id),
        action="delete",
    )

    return ok({"deleted": True})


# ---- EWT Classification ----

@router.post("/sessions/{session_id}/classify-ewt")
async def classify_session_ewt(
    session_id: str,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Classify session purchase transactions for EWT applicability."""
    from backend.services.withholding_classifier import classify_ewt_transactions

    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    txn_repo = TransactionRepository(db)
    all_txns = await txn_repo.find_all_by_session(session.id)

    # Only classify purchase transactions
    purchase_txns = [t for t in all_txns if t.source_type == "purchase_record"]
    if not purchase_txns:
        raise HTTPException(status_code=400, detail="No purchase transactions to classify")

    # Build supplier lookup
    supplier_repo = SupplierRepository(db)
    suppliers = await supplier_repo.find_by_tenant(user.tenant_id, limit=500)
    supplier_lookup = {s.tin: {
        "supplier_type": s.supplier_type,
        "default_ewt_rate": float(s.default_ewt_rate) if s.default_ewt_rate else None,
        "default_atc_code": s.default_atc_code,
    } for s in suppliers}

    txn_dicts = [
        {
            "description": t.description,
            "amount": float(t.amount),
            "tin": t.tin,
        }
        for t in purchase_txns
    ]

    results = await classify_ewt_transactions(txn_dicts, supplier_lookup)

    # Update transactions with EWT classification
    classified_count = 0
    for txn, result in zip(purchase_txns, results):
        if result.get("ewt_applicable"):
            ewt_rate = result.get("ewt_rate") or 0
            ewt_amount = float(txn.amount) * ewt_rate
            await txn_repo.update(
                txn,
                ewt_rate=ewt_rate,
                ewt_amount=ewt_amount,
                atc_code=result.get("atc_code"),
            )
            classified_count += 1
        else:
            await txn_repo.update(txn, ewt_rate=0, ewt_amount=0, atc_code=None)

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="reconciliation_session", entity_id=session.id,
        action="classify_ewt",
        changes={"classified": classified_count, "total": len(purchase_txns)},
    )

    return ok({"classified": classified_count, "total": len(purchase_txns)})


# ---- Certificate Generation ----

@router.get("/certificates")
async def list_certificates(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    period: str | None = None,
    supplier_id: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List withholding certificates."""
    repo = WithholdingCertificateRepository(db)
    offset = (page - 1) * limit
    certs = await repo.find_by_tenant(
        user.tenant_id,
        offset=offset,
        limit=limit,
        period=period,
        supplier_id=uuid.UUID(supplier_id) if supplier_id else None,
    )
    total = await repo.count_by_tenant(user.tenant_id, period=period)

    # Fetch supplier names
    supplier_repo = SupplierRepository(db)
    supplier_names: dict[str, str] = {}
    for cert in certs:
        sid = str(cert.supplier_id)
        if sid not in supplier_names:
            s = await supplier_repo.get_by_id(cert.supplier_id)
            supplier_names[sid] = s.name if s else ""

    return ok(
        [_certificate_response(c, supplier_names.get(str(c.supplier_id))) for c in certs],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.post("/sessions/{session_id}/generate-certificates")
async def generate_certificates(
    session_id: str,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Generate BIR 2307 certificates from session EWT-classified transactions."""
    from backend.services.withholding_generator import generate_bir_2307_pdf

    sess_repo = ReconciliationSessionRepository(db)
    session = await sess_repo.get_by_id(uuid.UUID(session_id))
    if not session or session.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Session not found")

    txn_repo = TransactionRepository(db)
    all_txns = await txn_repo.find_all_by_session(session.id)

    # Filter to EWT-applicable purchase transactions
    ewt_txns = [
        t for t in all_txns
        if t.source_type == "purchase_record"
        and t.ewt_rate is not None
        and float(t.ewt_rate) > 0
    ]
    if not ewt_txns:
        raise HTTPException(status_code=400, detail="No EWT-classified transactions found. Run classify-ewt first.")

    quarter = _period_to_quarter(session.period)
    tenant_info = {
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
    }

    # Group transactions by supplier TIN
    supplier_groups: dict[str, list] = {}
    for t in ewt_txns:
        tin = t.tin or "unknown"
        supplier_groups.setdefault(tin, []).append(t)

    cert_repo = WithholdingCertificateRepository(db)
    supplier_repo = SupplierRepository(db)

    # Clear previous certificates for this session
    await cert_repo.delete_by_session(session.id)

    created_certs = []
    for tin, txns in supplier_groups.items():
        # Find or create supplier
        supplier = await supplier_repo.find_by_tin(user.tenant_id, tin) if tin != "unknown" else None

        if not supplier:
            # Auto-create supplier from transaction data
            supplier = await supplier_repo.create(
                tenant_id=user.tenant_id,
                tin=tin,
                name=txns[0].description or f"Supplier ({tin})",
                supplier_type="corporation",
            )

        # Aggregate by ATC code
        atc_groups: dict[str, dict] = {}
        for t in txns:
            atc = t.atc_code or "WC120"
            if atc not in atc_groups:
                atc_groups[atc] = {"income": Decimal("0"), "tax": Decimal("0"), "rate": t.ewt_rate}
            atc_groups[atc]["income"] += Decimal(str(t.amount))
            atc_groups[atc]["tax"] += Decimal(str(t.ewt_amount or 0))

        for atc_code, agg in atc_groups.items():
            from backend.services.ewt_rates import get_income_type

            cert_data = {
                "tenant_id": user.tenant_id,
                "session_id": session.id,
                "supplier_id": supplier.id,
                "period": session.period,
                "quarter": quarter,
                "atc_code": atc_code,
                "income_type": get_income_type(atc_code),
                "income_amount": agg["income"],
                "ewt_rate": agg["rate"],
                "tax_withheld": agg["tax"],
                "status": "generated",
            }

            # Generate PDF
            supplier_info = {
                "tin": supplier.tin,
                "name": supplier.name,
                "address": supplier.address or "",
                "supplier_type": supplier.supplier_type,
            }
            file_path = generate_bir_2307_pdf(
                {**cert_data, "income_amount": float(agg["income"]), "tax_withheld": float(agg["tax"]), "ewt_rate": float(agg["rate"])},
                supplier_info,
                tenant_info,
            )
            cert_data["file_path"] = file_path

            cert = await cert_repo.create(**cert_data)
            created_certs.append(cert)

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        entity_type="reconciliation_session", entity_id=session.id,
        action="generate_certificates",
        changes={"certificates_created": len(created_certs)},
    )

    return ok({
        "certificates_created": len(created_certs),
        "suppliers_processed": len(supplier_groups),
    })


@router.get("/certificates/{cert_id}/download")
async def download_certificate(
    cert_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Download a BIR 2307 certificate PDF."""
    repo = WithholdingCertificateRepository(db)
    cert = await repo.get_by_id(uuid.UUID(cert_id))
    if not cert or cert.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if not cert.file_path:
        raise HTTPException(status_code=404, detail="PDF not generated")

    return FileResponse(
        cert.file_path,
        media_type="application/pdf",
        filename=f"BIR2307_{cert.quarter}_{cert.atc_code}.pdf",
    )


# ---- SAWT ----

@router.get("/sawt")
async def get_sawt_summary(
    period: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get SAWT summary for a period."""
    repo = WithholdingCertificateRepository(db)
    certs = await repo.find_by_tenant(user.tenant_id, period=period, limit=500)

    supplier_repo = SupplierRepository(db)
    entries = []
    for cert in certs:
        s = await supplier_repo.get_by_id(cert.supplier_id)
        entries.append({
            "supplier_tin": s.tin if s else "",
            "supplier_name": s.name if s else "",
            "atc_code": cert.atc_code,
            "income_type": cert.income_type,
            "income_amount": float(cert.income_amount),
            "ewt_rate": float(cert.ewt_rate),
            "tax_withheld": float(cert.tax_withheld),
            "quarter": cert.quarter,
            "period": cert.period,
        })

    total_income = sum(e["income_amount"] for e in entries)
    total_tax = sum(e["tax_withheld"] for e in entries)

    return ok({
        "period": period,
        "entries": entries,
        "total_income": total_income,
        "total_tax_withheld": total_tax,
        "total_entries": len(entries),
    })


@router.get("/sawt/download")
async def download_sawt(
    period: str = Query(...),
    format: str = Query(default="csv"),
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_session),
):
    """Download SAWT as CSV or PDF."""
    from backend.services.withholding_generator import generate_sawt_csv, generate_sawt_pdf

    repo = WithholdingCertificateRepository(db)
    certs = await repo.find_by_tenant(user.tenant_id, period=period, limit=500)
    if not certs:
        raise HTTPException(status_code=404, detail="No certificates found for this period")

    supplier_repo = SupplierRepository(db)
    entries = []
    for cert in certs:
        s = await supplier_repo.get_by_id(cert.supplier_id)
        entries.append({
            "supplier_tin": s.tin if s else "",
            "supplier_name": s.name if s else "",
            "atc_code": cert.atc_code,
            "income_type": cert.income_type,
            "income_amount": float(cert.income_amount),
            "ewt_rate": float(cert.ewt_rate),
            "tax_withheld": float(cert.tax_withheld),
            "quarter": cert.quarter,
            "period": cert.period,
        })

    tenant_info = {
        "company_name": tenant.company_name,
        "tin_number": tenant.tin_number,
        "rdo_code": tenant.rdo_code,
    }

    if format == "pdf":
        filepath = generate_sawt_pdf(entries, tenant_info, period)
        return FileResponse(
            filepath,
            media_type="application/pdf",
            filename=f"SAWT_{period}.pdf",
        )

    # Default: CSV
    csv_content = generate_sawt_csv(entries, tenant_info, period)
    import io
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=SAWT_{period}.csv"},
    )


# ---- EWT Summary ----

@router.get("/ewt-summary")
async def get_ewt_summary(
    period: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get monthly EWT summary."""
    repo = WithholdingCertificateRepository(db)
    summary = await repo.get_ewt_summary(user.tenant_id, period)
    return ok(summary)


# ---- EWT Rates Reference ----

@router.get("/ewt-rates")
async def list_ewt_rates():
    """List all EWT rates for reference."""
    from backend.services.ewt_rates import list_rates
    return ok(list_rates())
