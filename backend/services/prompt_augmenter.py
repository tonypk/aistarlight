"""Prompt augmenter — generates tenant-specific prompt supplements from learned rules.

Adds to the LLM classification system prompt to encode learned corrections,
preventing the same mistakes from recurring.

Security: Sanitizes all user-derived content to prevent prompt injection.
"""

import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.correction_repo import CorrectionRepository
from backend.repositories.correction_rule_repo import CorrectionRuleRepository

logger = logging.getLogger(__name__)

MAX_AUGMENT_RULES = 15
MAX_RECENT_CORRECTIONS = 10


def _sanitize(text: str) -> str:
    """Sanitize user-derived text to prevent prompt injection."""
    if not text:
        return ""
    # Remove potential instruction-like patterns
    sanitized = re.sub(r"(ignore|disregard|forget)\s+(previous|above|all)", "", text, flags=re.IGNORECASE)
    # Remove markdown/code markers that could confuse the model
    sanitized = re.sub(r"```[\s\S]*?```", "", sanitized)
    # Remove excessive whitespace
    sanitized = " ".join(sanitized.split())
    # Truncate
    return sanitized[:200]


async def generate_prompt_supplement(
    db: AsyncSession, tenant_id: uuid.UUID
) -> str:
    """Generate a tenant-specific prompt supplement from active rules and recent corrections.

    Returns a string to append to the LLM system prompt, or empty string if none.
    """
    rule_repo = CorrectionRuleRepository(db)
    active_rules = await rule_repo.find_active(tenant_id)

    if not active_rules:
        return ""

    lines = [
        "\n--- Tenant-Specific Classification Rules (learned from accountant corrections) ---"
    ]

    for rule in active_rules[:MAX_AUGMENT_RULES]:
        criteria = rule.match_criteria or {}
        field = _sanitize(str(criteria.get("field", "")))
        operator = _sanitize(str(criteria.get("operator", "")))
        value = criteria.get("value", "")

        if isinstance(value, list):
            value_str = ", ".join(_sanitize(str(v)) for v in value[:5])
        else:
            value_str = _sanitize(str(value))

        correction_field = _sanitize(rule.correction_field)
        correction_value = _sanitize(rule.correction_value)
        confidence = float(rule.confidence)

        lines.append(
            f"- When {field} {operator} [{value_str}]: "
            f"set {correction_field}={correction_value} "
            f"(confidence: {confidence:.0%}, from {rule.source_correction_count} corrections)"
        )

    # Also add a few recent high-frequency corrections as hints
    correction_repo = CorrectionRepository(db)
    stats = await correction_repo.get_correction_stats(tenant_id)
    frequent = [s for s in stats if s["count"] >= 2][:MAX_RECENT_CORRECTIONS]

    if frequent:
        lines.append("\n--- Frequent Correction Patterns ---")
        for s in frequent:
            field = _sanitize(s["field_name"])
            value = _sanitize(s["new_value"])
            lines.append(
                f"- Accountant frequently corrects {field} to '{value}' ({s['count']} times)"
            )

    lines.append("--- End Tenant Rules ---\n")

    supplement = "\n".join(lines)
    logger.debug("Generated prompt supplement: %d chars for tenant %s", len(supplement), tenant_id)
    return supplement
