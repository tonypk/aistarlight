"""Receipt processing orchestrator: upload -> OCR -> parse -> transactions -> report."""

import logging
import os
import uuid
from datetime import date as date_type
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.repositories.receipt_repo import ReceiptBatchRepository
from backend.repositories.reconciliation_repo import ReconciliationSessionRepository
from backend.repositories.transaction import TransactionRepository
from backend.services.receipt_ocr import ocr_image
from backend.services.receipt_parser import (
    ParsedField,
    needs_llm,
    parse_receipt,
    resolve_ambiguous_fields,
)

logger = logging.getLogger(__name__)

RECEIPT_UPLOAD_DIR = "receipts"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def _save_receipt_image(content: bytes, original_filename: str) -> tuple[str, str]:
    """Save receipt image to uploads/receipts/ with a UUID filename.

    Returns (file_path, file_id).
    """
    ext = Path(original_filename).suffix.lower() or ".jpg"
    file_id = str(uuid.uuid4())
    receipt_dir = os.path.join(settings.upload_dir, RECEIPT_UPLOAD_DIR)
    os.makedirs(receipt_dir, exist_ok=True)
    file_path = os.path.join(receipt_dir, f"{file_id}{ext}")

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, file_id


def _parse_date_safe(date_str: str | None) -> date_type | None:
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        parts = date_str[:10].split("-")
        return date_type(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


async def process_receipt_batch(
    images: list[tuple[str, bytes]],
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    period: str,
    report_type: str,
    db: AsyncSession,
) -> dict:
    """Process a batch of receipt images end-to-end.

    Args:
        images: List of (filename, content_bytes) tuples.
        tenant_id: Tenant UUID.
        user_id: User UUID.
        period: Tax period (YYYY-MM).
        report_type: BIR form type (e.g., "BIR_2550M").
        db: Database session.

    Returns:
        ReceiptBatch ORM object.
    """
    from backend.models.receipt import ReceiptBatch as ReceiptBatchModel

    batch_repo = ReceiptBatchRepository(db)

    # 1. Create batch record
    batch = await batch_repo.create(
        tenant_id=tenant_id,
        user_id=user_id,
        status="processing",
        total_images=len(images),
        processed_count=0,
        period=period,
        report_type=report_type,
        results=[],
    )

    receipt_results = []
    transactions_data = []

    # 2. Process each image
    for idx, (filename, content) in enumerate(images):
        result_entry = {"filename": filename, "index": idx, "status": "processing"}
        try:
            # Save image
            file_path, file_id = _save_receipt_image(content, filename)

            # OCR
            ocr_result = await ocr_image(file_path)
            ocr_text = ocr_result.get("text", "")
            ocr_lines = ocr_result.get("lines", [])

            if not ocr_text.strip():
                result_entry["status"] = "failed"
                result_entry["error"] = "No text extracted from image"
                receipt_results.append(result_entry)
                continue

            # Rule-based parsing
            parsed = parse_receipt(ocr_text, ocr_lines)

            # Confidence gating + LLM for ambiguous fields
            ambiguous = needs_llm(parsed)
            llm_fields_resolved = []
            if ambiguous:
                resolved = await resolve_ambiguous_fields(ocr_text, ambiguous)
                for field_name, value in resolved.items():
                    if field_name == "category":
                        parsed.category = ParsedField(value=value, confidence=0.85)
                    elif field_name == "vat_type":
                        parsed.vat_type = ParsedField(value=value, confidence=0.85)
                    elif field_name == "vendor_name":
                        parsed.vendor_name = ParsedField(value=value, confidence=0.80)
                    elif field_name == "total_amount":
                        parsed.total_amount = ParsedField(value=value, confidence=0.80)
                    llm_fields_resolved.append(field_name)

            # Calculate overall confidence
            confidences = [
                parsed.total_amount.confidence,
                parsed.vat_type.confidence,
                parsed.category.confidence,
            ]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Build transaction data
            total = float(parsed.total_amount.value or 0)
            vat_amt = float(parsed.vat_amount.value or 0)
            vat_type = str(parsed.vat_type.value or "vatable")

            # If no VAT amount extracted but is vatable, calculate 12%
            if vat_amt == 0 and total > 0 and vat_type == "vatable":
                vat_amt = round(total / 1.12 * 0.12, 2)

            transactions_data.append({
                "tenant_id": tenant_id,
                "source_type": "purchase_record",
                "source_file_id": file_id,
                "row_index": idx,
                "date": _parse_date_safe(str(parsed.date.value) if parsed.date.value else None),
                "description": str(parsed.vendor_name.value or filename),
                "amount": total,
                "vat_amount": vat_amt,
                "vat_type": vat_type,
                "category": str(parsed.category.value or "goods"),
                "tin": str(parsed.tin.value) if parsed.tin.value else None,
                "confidence": round(overall_confidence, 2),
                "classification_source": "receipt_ocr",
                "raw_data": {
                    "ocr_text": ocr_text[:2000],
                    "receipt_number": parsed.receipt_number.value,
                    "vatable_sales": parsed.vatable_sales.value,
                    "llm_fields_resolved": llm_fields_resolved,
                },
            })

            result_entry.update({
                "status": "success",
                "vendor_name": parsed.vendor_name.value,
                "tin": parsed.tin.value,
                "date": parsed.date.value,
                "total_amount": total,
                "vat_amount": vat_amt,
                "vat_type": vat_type,
                "category": parsed.category.value,
                "receipt_number": parsed.receipt_number.value,
                "overall_confidence": round(overall_confidence, 2),
                "llm_fields_resolved": llm_fields_resolved,
            })

        except Exception as e:
            logger.error("Failed to process receipt %s: %s", filename, e)
            result_entry["status"] = "failed"
            result_entry["error"] = f"Processing failed: {type(e).__name__}"

        receipt_results.append(result_entry)

        # Update progress
        await batch_repo.update(
            batch,
            processed_count=idx + 1,
            results=receipt_results,
        )

    # 3. Create reconciliation session + transactions
    if not transactions_data:
        await batch_repo.update(batch, status="failed", error_message="No receipts could be parsed")
        return batch

    try:
        sess_repo = ReconciliationSessionRepository(db)
        session = await sess_repo.create(
            tenant_id=tenant_id,
            created_by=user_id,
            period=period,
            status="classified",
            source_files=[{
                "file_id": str(batch.id),
                "filename": f"receipt_batch_{batch.id}",
                "file_type": "receipt_ocr",
                "row_count": len(transactions_data),
            }],
        )

        # Set session_id on all transactions
        for txn in transactions_data:
            txn["session_id"] = session.id

        txn_repo = TransactionRepository(db)
        await txn_repo.bulk_create(transactions_data)

        # 4. Generate report
        report_id = None
        try:
            report_id = await _generate_report(
                session_id=session.id,
                tenant_id=tenant_id,
                user_id=user_id,
                period=period,
                report_type=report_type,
                transactions_data=transactions_data,
                db=db,
            )
        except Exception as e:
            logger.error("Report generation failed: %s", e)

        # 5. Finalize batch
        await batch_repo.update(
            batch,
            status="completed",
            session_id=session.id,
            report_id=report_id,
            results=receipt_results,
        )

        if report_id:
            await sess_repo.update(session, report_id=report_id)

    except Exception as e:
        logger.error("Batch processing failed: %s", e)
        await batch_repo.update(
            batch,
            status="failed",
            error_message=f"Processing failed: {type(e).__name__}",
            results=receipt_results,
        )

    return batch


async def _generate_report(
    session_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    period: str,
    report_type: str,
    transactions_data: list[dict],
    db: AsyncSession,
) -> uuid.UUID | None:
    """Generate a BIR report from parsed receipt transactions."""
    from backend.repositories.report import ReportRepository
    from backend.services.report_generator import generate_pdf_report
    from backend.services.tax_engine import calculate_report

    # Separate sales and purchases for tax engine
    sales_data = [
        {"amount": t["amount"], "vat_amount": t["vat_amount"], "vat_type": t["vat_type"], "category": t["category"]}
        for t in transactions_data
        if t["source_type"] == "sales_record"
    ]
    purchases_data = [
        {"amount": t["amount"], "vat_amount": t["vat_amount"], "vat_type": t["vat_type"], "category": t["category"]}
        for t in transactions_data
        if t["source_type"] == "purchase_record"
    ]

    calculated = await calculate_report(
        form_type=report_type,
        sales_data=sales_data,
        purchases_data=purchases_data,
        db=db,
    )
    calculated["period"] = period

    # Get tenant info for PDF
    from sqlalchemy import select
    from backend.models.tenant import Tenant
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    tenant_info = {
        "company_name": tenant.company_name if tenant else "",
        "tin_number": tenant.tin_number if tenant else "",
        "rdo_code": tenant.rdo_code if tenant else "",
    }

    file_path = generate_pdf_report(report_type, calculated, tenant_info)

    report_repo = ReportRepository(db)
    report = await report_repo.create(
        tenant_id=tenant_id,
        report_type=report_type,
        period=period,
        status="draft",
        input_data={
            "source": "receipt_ocr",
            "session_id": str(session_id),
            "purchases_count": len(purchases_data),
        },
        calculated_data=calculated,
        file_path=file_path,
        created_by=user_id,
    )

    return report.id
