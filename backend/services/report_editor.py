"""Report editing service — applies field overrides and recalculates dependent lines."""

import copy
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.report import Report
from backend.models.workflow import is_editable
from backend.repositories.report import ReportRepository
from backend.services.audit_logger import log_action
from backend.services.report_generator import generate_pdf_report

# BIR 2550M recalculation dependency graph
# Maps computed field → formula (using field references)
BIR_2550M_FORMULAS: dict[str, list[str]] = {
    "line_5_total_sales": [
        "line_1_vatable_sales",
        "line_2_sales_to_government",
        "line_3_zero_rated_sales",
        "line_4_exempt_sales",
    ],
    "line_6_output_vat": ["line_1_vatable_sales"],  # * 0.12
    "line_6a_output_vat_government": ["line_2_sales_to_government"],  # * 0.05
    "line_6b_total_output_vat": ["line_6_output_vat", "line_6a_output_vat_government"],
    "line_11_total_input_vat": [
        "line_7_input_vat_goods",
        "line_8_input_vat_capital",
        "line_9_input_vat_services",
        "line_10_input_vat_imports",
    ],
    "line_12_vat_payable": ["line_6b_total_output_vat", "line_11_total_input_vat"],  # 6B - 11
    "line_14_net_vat_payable": ["line_12_vat_payable", "line_13_less_tax_credits"],  # max(12 - 13, 0)
    "line_16_total_amount_due": ["line_14_net_vat_payable", "line_15_add_penalties"],
}


def _d(val: str | None) -> Decimal:
    """Convert string value to Decimal safely."""
    if val is None:
        return Decimal("0")
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


def recalculate_bir_2550m(data: dict[str, str]) -> dict[str, str]:
    """Recalculate all computed fields from current values.

    Follows the BIR 2550M calculation chain in order.
    Returns a new dict with updated computed fields.
    """
    result = dict(data)

    # Line 5: Total Sales = sum(1,2,3,4)
    result["line_5_total_sales"] = str(
        _d(result.get("line_1_vatable_sales"))
        + _d(result.get("line_2_sales_to_government"))
        + _d(result.get("line_3_zero_rated_sales"))
        + _d(result.get("line_4_exempt_sales"))
    )

    # Line 6: Output VAT = Line 1 * 12%
    result["line_6_output_vat"] = str(_d(result.get("line_1_vatable_sales")) * Decimal("0.12"))

    # Line 6A: Output VAT Gov = Line 2 * 5%
    result["line_6a_output_vat_government"] = str(
        _d(result.get("line_2_sales_to_government")) * Decimal("0.05")
    )

    # Line 6B: Total Output = 6 + 6A
    result["line_6b_total_output_vat"] = str(
        _d(result["line_6_output_vat"]) + _d(result["line_6a_output_vat_government"])
    )

    # Line 11: Total Input = sum(7,8,9,10)
    result["line_11_total_input_vat"] = str(
        _d(result.get("line_7_input_vat_goods"))
        + _d(result.get("line_8_input_vat_capital"))
        + _d(result.get("line_9_input_vat_services"))
        + _d(result.get("line_10_input_vat_imports"))
    )

    # Line 12: VAT Payable = 6B - 11
    result["line_12_vat_payable"] = str(
        _d(result["line_6b_total_output_vat"]) - _d(result["line_11_total_input_vat"])
    )

    # Line 14: Net VAT Payable = max(12 - 13, 0)
    net_raw = _d(result["line_12_vat_payable"]) - _d(result.get("line_13_less_tax_credits"))
    result["line_14_net_vat_payable"] = str(max(net_raw, Decimal("0")))

    # Tax credit carried forward
    result["tax_credit_carried_forward"] = str(max(-net_raw, Decimal("0")))

    # Line 16: Total Amount Due = 14 + 15
    result["line_16_total_amount_due"] = str(
        _d(result["line_14_net_vat_payable"]) + _d(result.get("line_15_add_penalties"))
    )

    # Update legacy compatibility keys
    result["vatable_sales"] = result.get("line_1_vatable_sales", "0")
    result["vat_exempt_sales"] = result.get("line_4_exempt_sales", "0")
    result["zero_rated_sales"] = result.get("line_3_zero_rated_sales", "0")
    result["total_sales"] = result["line_5_total_sales"]
    result["output_vat"] = result["line_6_output_vat"]
    result["input_vat_goods"] = result.get("line_7_input_vat_goods", "0")
    result["input_vat_services"] = result.get("line_9_input_vat_services", "0")
    result["input_vat_capital"] = result.get("line_8_input_vat_capital", "0")
    result["total_input_vat"] = result["line_11_total_input_vat"]
    result["vat_payable"] = result["line_12_vat_payable"]
    result["net_vat_payable"] = result["line_14_net_vat_payable"]

    return result


class VersionConflictError(Exception):
    """Raised when optimistic lock version does not match."""


class NotEditableError(Exception):
    """Raised when a report is in a status that cannot be edited."""


async def apply_field_overrides(
    db: AsyncSession,
    *,
    report: Report,
    field_overrides: dict[str, str],
    recalculate: bool = True,
    notes: str | None = None,
    expected_version: int,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    tenant_info: dict[str, Any],
) -> Report:
    """Apply field overrides to a report, optionally recalculate, regenerate PDF, and log audit.

    Args:
        db: Database session.
        report: The report to edit.
        field_overrides: Dict of field_name → new_value.
        recalculate: Whether to recalculate dependent fields after override.
        notes: Optional note explaining the edit.
        expected_version: Optimistic lock — must match current version.
        user_id: The user performing the edit.
        tenant_id: The tenant owning the report.
        tenant_info: Tenant info for PDF regeneration.

    Returns:
        The updated Report.

    Raises:
        NotEditableError: If report status doesn't allow editing.
        VersionConflictError: If report.version != expected_version.
    """
    if not is_editable(report.status):
        raise NotEditableError(f"Report in status '{report.status}' cannot be edited")

    if report.version != expected_version:
        raise VersionConflictError(
            f"Version conflict: expected {expected_version}, current {report.version}"
        )

    # Snapshot original calculated data on first edit
    if report.original_calculated_data is None:
        report.original_calculated_data = copy.deepcopy(report.calculated_data)

    # Build merged data: start with current calculated, apply overrides
    current_data: dict[str, str] = dict(report.calculated_data or {})
    old_values: dict[str, str] = {}

    for field, new_value in field_overrides.items():
        old_values[field] = current_data.get(field, "")
        current_data[field] = new_value

    # Recalculate dependent fields if requested
    if recalculate and report.report_type in ("BIR_2550M", "BIR_2550Q"):
        current_data = recalculate_bir_2550m(current_data)

    # Preserve period
    current_data["period"] = report.period

    # Track overrides (cumulative)
    all_overrides = dict(report.overrides or {})
    all_overrides.update(field_overrides)

    # Regenerate PDF
    file_path = generate_pdf_report(report.report_type, current_data, tenant_info)

    # Build audit changes
    audit_changes: dict[str, dict[str, str]] = {}
    for field, new_value in field_overrides.items():
        old = old_values.get(field, "")
        if old != new_value:
            audit_changes[field] = {"old": old, "new": new_value}

    # Update report
    repo = ReportRepository(db)
    report = await repo.update(
        report,
        calculated_data=current_data,
        overrides=all_overrides,
        file_path=file_path,
        version=report.version + 1,
        updated_by=user_id,
        updated_at=datetime.now(UTC),
        notes=notes or report.notes,
    )

    # Write audit log
    if audit_changes:
        await log_action(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
            entity_type="report",
            entity_id=report.id,
            action="edit",
            changes=audit_changes,
            comment=notes,
        )

    return report
