"""Report status machine and workflow definitions."""

from enum import StrEnum


class ReportStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FILED = "filed"
    ARCHIVED = "archived"


# Valid state transitions: {from_status: [allowed_to_statuses]}
VALID_TRANSITIONS: dict[ReportStatus, list[ReportStatus]] = {
    ReportStatus.DRAFT: [ReportStatus.REVIEW],
    ReportStatus.REVIEW: [ReportStatus.APPROVED, ReportStatus.REJECTED, ReportStatus.DRAFT],
    ReportStatus.APPROVED: [ReportStatus.FILED, ReportStatus.REVIEW],
    ReportStatus.REJECTED: [ReportStatus.DRAFT],
    ReportStatus.FILED: [ReportStatus.ARCHIVED],
    ReportStatus.ARCHIVED: [],
}

# Statuses where editing is allowed
EDITABLE_STATUSES: set[ReportStatus] = {
    ReportStatus.DRAFT,
    ReportStatus.REVIEW,
    ReportStatus.REJECTED,
}


def is_valid_transition(from_status: str, to_status: str) -> bool:
    """Check if a status transition is allowed."""
    try:
        from_s = ReportStatus(from_status)
        to_s = ReportStatus(to_status)
    except ValueError:
        return False
    return to_s in VALID_TRANSITIONS.get(from_s, [])


def is_editable(status: str) -> bool:
    """Check if a report in this status can be edited."""
    try:
        return ReportStatus(status) in EDITABLE_STATUSES
    except ValueError:
        return False
