"""Anomaly detection for reconciliation sessions.

Five pure-function detectors (no DB, no I/O) + one orchestrator.
All detectors return list of DetectedAnomaly dicts.
"""

import logging
import statistics
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DetectedAnomaly:
    """Anomaly detected during analysis."""

    anomaly_type: str
    severity: str  # high / medium / low
    description: str
    details: dict = field(default_factory=dict)
    transaction_id: uuid.UUID | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["transaction_id"]:
            d["transaction_id"] = str(d["transaction_id"])
        return d


# --- Detector 1: Duplicate transactions ---

def detect_duplicate_transactions(
    transactions: list[dict],
) -> list[DetectedAnomaly]:
    """Find transactions with identical date + amount + description."""
    anomalies = []
    seen: dict[str, list[dict]] = {}

    for txn in transactions:
        key = f"{txn.get('date')}|{txn.get('amount')}|{(txn.get('description') or '').strip().lower()}"
        if key not in seen:
            seen[key] = []
        seen[key].append(txn)

    for key, group in seen.items():
        if len(group) > 1:
            ids = [str(t.get("id", "")) for t in group]
            anomalies.append(DetectedAnomaly(
                anomaly_type="duplicate",
                severity="medium",
                description=f"Possible duplicate: {len(group)} transactions with same date/amount/description",
                details={
                    "transaction_ids": ids,
                    "count": len(group),
                    "date": group[0].get("date"),
                    "amount": group[0].get("amount"),
                    "description": (group[0].get("description") or "")[:100],
                },
                transaction_id=uuid.UUID(ids[0]) if ids[0] else None,
            ))

    return anomalies


# --- Detector 2: VAT mismatches ---

def detect_vat_mismatches(
    transactions: list[dict],
    vat_rate: float = 0.12,
    tolerance: float = 0.02,
) -> list[DetectedAnomaly]:
    """Find transactions where VAT amount doesn't match expected rate."""
    anomalies = []

    for txn in transactions:
        amount = float(txn.get("amount", 0))
        vat_amount = float(txn.get("vat_amount", 0))
        vat_type = txn.get("vat_type", "vatable")

        if vat_type != "vatable" or amount <= 0:
            continue

        expected_vat = amount * vat_rate
        if vat_amount > 0 and abs(vat_amount - expected_vat) > (expected_vat * tolerance):
            anomalies.append(DetectedAnomaly(
                anomaly_type="vat_mismatch",
                severity="high",
                description=f"VAT mismatch: expected ~{expected_vat:.2f} but found {vat_amount:.2f}",
                details={
                    "amount": amount,
                    "vat_amount": vat_amount,
                    "expected_vat": round(expected_vat, 2),
                    "difference": round(abs(vat_amount - expected_vat), 2),
                    "vat_type": vat_type,
                },
                transaction_id=uuid.UUID(str(txn["id"])) if txn.get("id") else None,
            ))

    return anomalies


# --- Detector 3: Incomplete TINs ---

def detect_incomplete_tins(
    transactions: list[dict],
    required_threshold: float = 1000.0,
) -> list[DetectedAnomaly]:
    """Find high-value transactions without a TIN."""
    anomalies = []

    for txn in transactions:
        amount = float(txn.get("amount", 0))
        tin = txn.get("tin")

        if amount >= required_threshold and (not tin or tin.strip().lower() in ("", "none", "nan")):
            anomalies.append(DetectedAnomaly(
                anomaly_type="incomplete_tin",
                severity="medium",
                description=f"Missing TIN for transaction of {amount:,.2f} PHP",
                details={
                    "amount": amount,
                    "description": (txn.get("description") or "")[:100],
                    "date": txn.get("date"),
                },
                transaction_id=uuid.UUID(str(txn["id"])) if txn.get("id") else None,
            ))

    return anomalies


# --- Detector 4: Unusual amounts ---

def detect_unusual_amounts(
    transactions: list[dict],
    z_score_threshold: float = 3.0,
) -> list[DetectedAnomaly]:
    """Find transactions with amounts significantly different from the mean (z-score)."""
    amounts = [float(t.get("amount", 0)) for t in transactions if float(t.get("amount", 0)) > 0]

    if len(amounts) < 5:
        return []

    mean = statistics.mean(amounts)
    stdev = statistics.stdev(amounts)
    if stdev == 0:
        return []

    anomalies = []
    for txn in transactions:
        amount = float(txn.get("amount", 0))
        if amount <= 0:
            continue
        z_score = (amount - mean) / stdev
        if abs(z_score) >= z_score_threshold:
            anomalies.append(DetectedAnomaly(
                anomaly_type="unusual_amount",
                severity="medium" if abs(z_score) < 5.0 else "high",
                description=f"Unusual amount: {amount:,.2f} PHP (z-score: {z_score:.1f})",
                details={
                    "amount": amount,
                    "z_score": round(z_score, 2),
                    "mean": round(mean, 2),
                    "stdev": round(stdev, 2),
                    "description": (txn.get("description") or "")[:100],
                    "date": txn.get("date"),
                },
                transaction_id=uuid.UUID(str(txn["id"])) if txn.get("id") else None,
            ))

    return anomalies


# --- Detector 5: Missing invoices (bank vs records) ---

def detect_missing_invoices(
    bank_txns: list[dict],
    record_txns: list[dict],
    amount_tolerance: float = 0.01,
    date_tolerance_days: int = 3,
) -> list[DetectedAnomaly]:
    """Find bank transactions without matching sales/purchase records and vice versa."""
    anomalies = []

    def _parse_date(d: Any) -> date | None:
        if isinstance(d, date):
            return d
        if isinstance(d, str) and len(d) >= 10:
            try:
                parts = d[:10].split("-")
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                return None
        return None

    def _amounts_match(a: float, b: float) -> bool:
        return abs(a - b) <= max(amount_tolerance, abs(a) * 0.001)

    def _dates_match(d1: Any, d2: Any) -> bool:
        pd1 = _parse_date(d1)
        pd2 = _parse_date(d2)
        if pd1 is None or pd2 is None:
            return True  # If either date is missing, don't penalize
        return abs((pd1 - pd2).days) <= date_tolerance_days

    # Track matched record indices
    matched_records = set()

    for bank_txn in bank_txns:
        bank_amount = float(bank_txn.get("amount", 0))
        found = False
        for j, rec in enumerate(record_txns):
            if j in matched_records:
                continue
            rec_amount = float(rec.get("amount", 0))
            if _amounts_match(bank_amount, rec_amount) and _dates_match(
                bank_txn.get("date"), rec.get("date")
            ):
                matched_records.add(j)
                found = True
                break

        if not found and bank_amount > 0:
            txn_type = bank_txn.get("type", "debit")
            anomaly_type = "unmatched_deposit" if txn_type == "credit" else "unmatched_payment"
            anomalies.append(DetectedAnomaly(
                anomaly_type=anomaly_type,
                severity="high" if bank_amount >= 10000 else "medium",
                description=f"Bank {txn_type} of {bank_amount:,.2f} PHP has no matching record",
                details={
                    "bank_amount": bank_amount,
                    "bank_date": bank_txn.get("date"),
                    "bank_description": (bank_txn.get("description") or "")[:100],
                    "bank_reference": bank_txn.get("reference"),
                },
                transaction_id=uuid.UUID(str(bank_txn["id"])) if bank_txn.get("id") else None,
            ))

    # Check for records without bank matches
    for j, rec in enumerate(record_txns):
        if j not in matched_records:
            rec_amount = float(rec.get("amount", 0))
            if rec_amount > 0:
                anomalies.append(DetectedAnomaly(
                    anomaly_type="missing_invoice",
                    severity="medium",
                    description=f"Record of {rec_amount:,.2f} PHP has no matching bank transaction",
                    details={
                        "record_amount": rec_amount,
                        "record_date": rec.get("date"),
                        "record_description": (rec.get("description") or "")[:100],
                    },
                    transaction_id=uuid.UUID(str(rec["id"])) if rec.get("id") else None,
                ))

    return anomalies


# --- Orchestrator ---

async def run_anomaly_detection(
    session_id: uuid.UUID,
    transactions: list[dict],
    bank_transactions: list[dict] | None = None,
) -> list[DetectedAnomaly]:
    """Run all anomaly detectors on session transactions.

    Args:
        session_id: The reconciliation session ID.
        transactions: Classified transaction dicts (from DB, with 'id' field).
        bank_transactions: Optional bank statement transactions for cross-matching.

    Returns combined list of all detected anomalies.
    """
    all_anomalies: list[DetectedAnomaly] = []

    # 1. Duplicate detection
    all_anomalies.extend(detect_duplicate_transactions(transactions))

    # 2. VAT mismatch detection
    all_anomalies.extend(detect_vat_mismatches(transactions))

    # 3. Incomplete TIN detection
    all_anomalies.extend(detect_incomplete_tins(transactions))

    # 4. Unusual amount detection
    all_anomalies.extend(detect_unusual_amounts(transactions))

    # 5. Missing invoice detection (requires bank transactions)
    if bank_transactions:
        record_txns = [t for t in transactions if t.get("source_type") != "bank_statement"]
        all_anomalies.extend(
            detect_missing_invoices(
                bank_txns=bank_transactions,
                record_txns=record_txns,
            )
        )

    logger.info(
        "Anomaly detection for session %s: found %d anomalies",
        session_id,
        len(all_anomalies),
    )
    return all_anomalies
