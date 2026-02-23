"""Reconciliation engine: transaction matching, VAT summarization, BIR comparison.

Core workflow:
1. generate_vat_summary() — aggregate Output/Input VAT from classified transactions
2. match_transactions() — match sales/purchase records against bank entries
3. compare_with_declared() — line-by-line BIR 2550M comparison
4. reconcile() — orchestrate the full reconciliation
"""

import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VatSummary:
    """Aggregated VAT summary from classified transactions."""

    period: str
    # Output VAT (Sales)
    vatable_sales: Decimal = Decimal("0")
    sales_to_government: Decimal = Decimal("0")
    zero_rated_sales: Decimal = Decimal("0")
    vat_exempt_sales: Decimal = Decimal("0")
    total_sales: Decimal = Decimal("0")
    output_vat: Decimal = Decimal("0")
    output_vat_government: Decimal = Decimal("0")
    total_output_vat: Decimal = Decimal("0")
    # Input VAT (Purchases)
    input_vat_goods: Decimal = Decimal("0")
    input_vat_capital: Decimal = Decimal("0")
    input_vat_services: Decimal = Decimal("0")
    input_vat_imports: Decimal = Decimal("0")
    total_input_vat: Decimal = Decimal("0")
    # Net
    net_vat: Decimal = Decimal("0")
    # Stats
    transaction_count: int = 0
    classification_stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: str(v) if isinstance(v, Decimal) else v for k, v in asdict(self).items()}


@dataclass
class MatchResult:
    """Result of transaction matching."""

    matched_pairs: list[dict] = field(default_factory=list)
    unmatched_records: list[dict] = field(default_factory=list)
    unmatched_bank: list[dict] = field(default_factory=list)
    match_rate: float = 0.0


VAT_RATE = Decimal("0.12")
GOVT_VAT_RATE = Decimal("0.05")


def generate_vat_summary(transactions: list[dict], period: str) -> VatSummary:
    """Aggregate Output/Input VAT from classified transactions.

    Mirrors the logic in tax_engine.calculate_bir_2550m() but works on
    already-classified Transaction records.
    """
    summary = VatSummary(period=period)
    vat_type_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    for txn in transactions:
        source_type = txn.get("source_type", "")
        amount = Decimal(str(txn.get("amount", 0)))
        vat_amount = Decimal(str(txn.get("vat_amount", 0)))
        vat_type = str(txn.get("vat_type", "vatable")).lower().strip()
        category = str(txn.get("category", "goods")).lower().strip()

        vat_type_counts[vat_type] = vat_type_counts.get(vat_type, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
        summary.transaction_count += 1

        # Sales (source_type = sales_record or category = sale)
        if source_type == "sales_record" or category == "sale":
            if vat_type == "government":
                summary.sales_to_government += amount
                summary.output_vat_government += amount * GOVT_VAT_RATE
            elif vat_type == "zero_rated":
                summary.zero_rated_sales += amount
            elif vat_type == "exempt":
                summary.vat_exempt_sales += amount
            else:  # vatable
                summary.vatable_sales += amount
                summary.output_vat += amount * VAT_RATE

        # Purchases (source_type = purchase_record)
        elif source_type == "purchase_record":
            input_vat = vat_amount if vat_amount else amount * VAT_RATE
            if category == "capital":
                summary.input_vat_capital += input_vat
            elif category == "services":
                summary.input_vat_services += input_vat
            elif category == "imports":
                summary.input_vat_imports += input_vat
            else:  # goods
                summary.input_vat_goods += input_vat

    # Totals
    summary.total_sales = (
        summary.vatable_sales
        + summary.sales_to_government
        + summary.zero_rated_sales
        + summary.vat_exempt_sales
    )
    summary.total_output_vat = summary.output_vat + summary.output_vat_government
    summary.total_input_vat = (
        summary.input_vat_goods
        + summary.input_vat_capital
        + summary.input_vat_services
        + summary.input_vat_imports
    )
    summary.net_vat = summary.total_output_vat - summary.total_input_vat
    summary.classification_stats = {
        "by_vat_type": vat_type_counts,
        "by_category": category_counts,
    }

    return summary


def match_transactions(
    records: list[dict],
    bank_entries: list[dict],
    amount_tolerance: float = 0.01,
    date_tolerance_days: int = 3,
) -> MatchResult:
    """Match sales/purchase records against bank entries.

    Uses greedy matching: for each record, find the closest bank entry by
    amount (within tolerance) and date (within tolerance).
    """
    result = MatchResult()
    used_bank = set()

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

    for rec in records:
        rec_amount = float(rec.get("amount", 0))
        rec_date = _parse_date(rec.get("date"))
        best_match = None
        best_score = float("inf")

        for j, bank in enumerate(bank_entries):
            if j in used_bank:
                continue
            bank_amount = float(bank.get("amount", 0))
            bank_date = _parse_date(bank.get("date"))

            amount_diff = abs(rec_amount - bank_amount)
            if amount_diff > max(amount_tolerance, abs(rec_amount) * 0.001):
                continue

            date_diff = 0
            if rec_date and bank_date:
                date_diff = abs((rec_date - bank_date).days)
                if date_diff > date_tolerance_days:
                    continue

            score = amount_diff + date_diff * 0.01
            if score < best_score:
                best_score = score
                best_match = j

        if best_match is not None:
            used_bank.add(best_match)
            match_group = str(uuid.uuid4())
            result.matched_pairs.append({
                "match_group_id": match_group,
                "record_id": str(rec.get("id", "")),
                "bank_id": str(bank_entries[best_match].get("id", "")),
                "record_amount": rec_amount,
                "bank_amount": float(bank_entries[best_match].get("amount", 0)),
                "date_diff_days": abs(
                    ((_parse_date(rec.get("date")) or date.min)
                     - (_parse_date(bank_entries[best_match].get("date")) or date.min)).days
                ) if _parse_date(rec.get("date")) and _parse_date(bank_entries[best_match].get("date")) else None,
            })
        else:
            result.unmatched_records.append({
                "id": str(rec.get("id", "")),
                "amount": rec_amount,
                "date": rec.get("date"),
                "description": (rec.get("description") or "")[:100],
            })

    # Unmatched bank entries
    for j, bank in enumerate(bank_entries):
        if j not in used_bank:
            result.unmatched_bank.append({
                "id": str(bank.get("id", "")),
                "amount": float(bank.get("amount", 0)),
                "date": bank.get("date"),
                "description": (bank.get("description") or "")[:100],
            })

    total = len(records) + len(bank_entries)
    if total > 0:
        matched_count = len(result.matched_pairs) * 2
        result.match_rate = round(matched_count / total, 4)

    return result


def compare_with_declared(
    summary: VatSummary, declared_data: dict
) -> dict:
    """Compare computed VAT summary with declared BIR 2550M data.

    Returns line-by-line comparison with differences.
    """
    comparisons = []

    field_mapping = [
        ("line_1_vatable_sales", "vatable_sales", summary.vatable_sales),
        ("line_2_sales_to_government", "sales_to_government", summary.sales_to_government),
        ("line_3_zero_rated_sales", "zero_rated_sales", summary.zero_rated_sales),
        ("line_4_exempt_sales", "vat_exempt_sales", summary.vat_exempt_sales),
        ("line_5_total_sales", "total_sales", summary.total_sales),
        ("line_6_output_vat", "output_vat", summary.output_vat),
        ("line_6a_output_vat_government", "output_vat_government", summary.output_vat_government),
        ("line_6b_total_output_vat", "total_output_vat", summary.total_output_vat),
        ("line_7_input_vat_goods", "input_vat_goods", summary.input_vat_goods),
        ("line_8_input_vat_capital", "input_vat_capital", summary.input_vat_capital),
        ("line_9_input_vat_services", "input_vat_services", summary.input_vat_services),
        ("line_10_input_vat_imports", "input_vat_imports", summary.input_vat_imports),
        ("line_11_total_input_vat", "total_input_vat", summary.total_input_vat),
    ]

    total_diff = Decimal("0")

    for line_key, label, computed in field_mapping:
        # Try both naming conventions for the declared data
        declared_str = declared_data.get(line_key) or declared_data.get(label, "0")
        declared = Decimal(str(declared_str))
        diff = computed - declared
        total_diff += abs(diff)

        comparisons.append({
            "line": line_key,
            "label": label,
            "computed": str(computed),
            "declared": str(declared),
            "difference": str(diff),
            "match": abs(diff) < Decimal("0.01"),
        })

    matched_lines = sum(1 for c in comparisons if c["match"])

    return {
        "comparisons": comparisons,
        "matched_lines": matched_lines,
        "total_lines": len(comparisons),
        "total_difference": str(total_diff),
        "fully_matched": matched_lines == len(comparisons),
    }


async def reconcile(
    session_id: uuid.UUID,
    sales: list[dict],
    purchases: list[dict],
    bank: list[dict] | None,
    declared_report: dict | None,
    period: str,
    amount_tolerance: float = 0.01,
    date_tolerance_days: int = 3,
) -> dict:
    """Orchestrate full reconciliation.

    Args:
        session_id: Reconciliation session UUID.
        sales: Classified sales transactions.
        purchases: Classified purchase transactions.
        bank: Optional bank statement transactions.
        declared_report: Optional declared BIR report calculated_data for comparison.
        period: Tax period string (e.g. "2026-01").
        amount_tolerance: Amount matching tolerance.
        date_tolerance_days: Date matching tolerance in days.

    Returns reconciliation result dict.
    """
    # 1. Generate VAT summary
    all_transactions = sales + purchases
    summary = generate_vat_summary(all_transactions, period)

    # 2. Match transactions against bank
    match_stats = {}
    if bank:
        all_records = sales + purchases
        match_result = match_transactions(
            records=all_records,
            bank_entries=bank,
            amount_tolerance=amount_tolerance,
            date_tolerance_days=date_tolerance_days,
        )
        match_stats = {
            "matched_pairs": len(match_result.matched_pairs),
            "unmatched_records": len(match_result.unmatched_records),
            "unmatched_bank": len(match_result.unmatched_bank),
            "match_rate": match_result.match_rate,
            "pairs": match_result.matched_pairs,
            "unmatched_record_details": match_result.unmatched_records,
            "unmatched_bank_details": match_result.unmatched_bank,
        }
    else:
        match_stats = {
            "matched_pairs": 0,
            "unmatched_records": len(sales) + len(purchases),
            "unmatched_bank": 0,
            "match_rate": 0.0,
            "note": "No bank statement provided for matching",
        }

    # 3. Compare with declared report
    comparison = None
    if declared_report and declared_report.get("calculated_data"):
        comparison = compare_with_declared(summary, declared_report["calculated_data"])

    result = {
        "session_id": str(session_id),
        "period": period,
        "summary": summary.to_dict(),
        "comparison": comparison,
        "match_stats": match_stats,
    }

    logger.info(
        "Reconciliation for session %s: %d transactions, match_rate=%.1f%%",
        session_id,
        summary.transaction_count,
        match_stats.get("match_rate", 0) * 100,
    )

    return result
