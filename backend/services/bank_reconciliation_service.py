"""Bank reconciliation orchestrator service.

Coordinates file parsing, transaction matching, and AI analysis
into a single pipeline producing a BankReconciliationBatch result.
"""

import logging
import uuid
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.bank_recon import BankReconciliationBatch
from backend.repositories.bank_recon_repo import BankReconBatchRepository
from backend.services.bank_parser import auto_detect_and_parse
from backend.services.match_analyzer import (
    MatchSuggestion,
    MismatchExplanation,
    analyze_unmatched_entries,
)
from backend.services.reconciliation_engine import match_transactions

logger = logging.getLogger(__name__)


def _suggestion_to_dict(s: MatchSuggestion) -> dict:
    return {**asdict(s), "status": "pending"}


def _explanation_to_dict(e: MismatchExplanation) -> dict:
    return asdict(e)


async def _update_batch(
    repo: BankReconBatchRepository,
    batch: BankReconciliationBatch,
    **kwargs,
) -> BankReconciliationBatch:
    return await repo.update(batch, **kwargs)


async def process_bank_reconciliation(
    files: list[tuple[str, bytes]],
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    period: str,
    db: AsyncSession,
    session_id: uuid.UUID | None = None,
    amount_tolerance: float = 0.01,
    date_tolerance_days: int = 3,
    run_ai_analysis: bool = True,
) -> BankReconciliationBatch:
    """Run the full bank reconciliation pipeline.

    Steps:
    1. Create batch (status=pending)
    2. Parse each file → standardized entries (status=parsing)
    3. If session_id: fetch existing session transactions as records
    4. match_transactions() (status=matching)
    5. If run_ai_analysis: analyze_unmatched_entries() (status=analyzing)
    6. Persist results (status=completed)
    """
    repo = BankReconBatchRepository(db)

    # 1. Create batch
    batch = await repo.create(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by=user_id,
        session_id=session_id,
        status="pending",
        period=period,
        amount_tolerance=amount_tolerance,
        date_tolerance_days=date_tolerance_days,
    )
    await db.flush()

    try:
        # 2. Parse all files
        batch = await _update_batch(repo, batch, status="parsing")
        await db.flush()

        all_bank_entries: list[dict] = []
        source_files_info: list[dict] = []

        for filename, content in files:
            parse_result = await auto_detect_and_parse(content, filename)
            entries = parse_result.get("transactions", [])

            # Add index-based IDs for matching
            for i, entry in enumerate(entries):
                if not entry.get("id"):
                    entry["id"] = f"{filename}:{i}"

            all_bank_entries.extend(entries)

            source_files_info.append({
                "filename": filename,
                "file_type": parse_result.get("file_type", "unknown"),
                "format_detected": parse_result.get("format_detected", False),
                "bank_name": parse_result.get("bank_name"),
                "row_count": parse_result.get("row_count", 0),
            })

        batch = await _update_batch(
            repo,
            batch,
            source_files=source_files_info,
            total_entries=len(all_bank_entries),
            parse_summary={
                "total_files": len(files),
                "total_entries": len(all_bank_entries),
                "per_file": source_files_info,
            },
        )
        await db.flush()

        if not all_bank_entries:
            batch = await _update_batch(
                repo,
                batch,
                status="completed",
                match_result={
                    "matched_pairs": [],
                    "unmatched_records": [],
                    "unmatched_bank": [],
                    "match_rate": 0.0,
                    "note": "No entries parsed from uploaded files",
                },
            )
            await db.commit()
            return batch

        # 3. Fetch existing session transactions if linked
        existing_records: list[dict] = []
        if session_id:
            from backend.models.transaction import Transaction
            from sqlalchemy import select

            result = await db.execute(
                select(Transaction).where(
                    Transaction.session_id == session_id,
                    Transaction.source_type.in_(["sales_record", "purchase_record"]),
                )
            )
            txns = result.scalars().all()
            existing_records = [
                {
                    "id": str(t.id),
                    "date": t.date.isoformat() if t.date else None,
                    "description": t.description or "",
                    "amount": float(t.amount),
                    "type": "debit" if t.source_type == "purchase_record" else "credit",
                    "reference": None,
                }
                for t in txns
            ]

        # 4. Match transactions
        batch = await _update_batch(repo, batch, status="matching")
        await db.flush()

        match_result = match_transactions(
            records=existing_records,
            bank_entries=all_bank_entries,
            amount_tolerance=amount_tolerance,
            date_tolerance_days=date_tolerance_days,
        )

        match_result_dict = {
            "matched_pairs": match_result.matched_pairs,
            "unmatched_records": match_result.unmatched_records,
            "unmatched_bank": match_result.unmatched_bank,
            "match_rate": match_result.match_rate,
            "total_records": len(existing_records),
            "total_bank_entries": len(all_bank_entries),
        }

        batch = await _update_batch(repo, batch, match_result=match_result_dict)
        await db.flush()

        # 5. AI analysis of unmatched entries
        if run_ai_analysis and (
            match_result.unmatched_bank or match_result.unmatched_records
        ):
            batch = await _update_batch(repo, batch, status="analyzing")
            await db.flush()

            max_suggestions = getattr(settings, "max_ai_suggestions", 20)

            suggestions, explanations = await analyze_unmatched_entries(
                unmatched_bank=match_result.unmatched_bank,
                unmatched_records=match_result.unmatched_records,
                all_records=existing_records,
                all_bank=all_bank_entries,
                max_suggestions=max_suggestions,
            )

            batch = await _update_batch(
                repo,
                batch,
                ai_suggestions=[_suggestion_to_dict(s) for s in suggestions],
                ai_explanations=[_explanation_to_dict(e) for e in explanations],
            )
            await db.flush()

        # 6. Mark completed
        batch = await _update_batch(repo, batch, status="completed")
        await db.commit()

        logger.info(
            "Bank reconciliation batch %s completed: %d entries, match_rate=%.1f%%",
            batch.id,
            len(all_bank_entries),
            match_result.match_rate * 100,
        )

        return batch

    except Exception as e:
        logger.error("Bank reconciliation failed: %s", e)
        batch = await _update_batch(
            repo, batch, status="failed", error_message=str(e)[:500]
        )
        await db.commit()
        raise
