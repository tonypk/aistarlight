"""Correction pattern analyzer — detects repeated correction patterns and generates candidate rules.

When the same correction appears >= RULE_THRESHOLD times, a CorrectionRule candidate is generated.
"""

import logging
import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.correction_repo import CorrectionRepository
from backend.repositories.correction_rule_repo import CorrectionRuleRepository

logger = logging.getLogger(__name__)

RULE_THRESHOLD = 3  # Minimum corrections of same pattern to generate a rule


def _extract_keywords(descriptions: list[str]) -> list[str]:
    """Extract common keywords from a list of transaction descriptions."""
    if not descriptions:
        return []
    # Tokenize and find words appearing in >= 50% of descriptions
    word_counts: dict[str, int] = defaultdict(int)
    total = len(descriptions)
    for desc in descriptions:
        seen = set()
        for word in (desc or "").lower().split():
            word = word.strip(".,;:!?()[]{}\"'")
            if len(word) >= 3 and word not in seen:
                word_counts[word] += 1
                seen.add(word)
    threshold = max(1, total * 0.5)
    return sorted(
        [w for w, c in word_counts.items() if c >= threshold],
        key=lambda w: word_counts[w],
        reverse=True,
    )[:10]


def _detect_patterns(corrections: list[dict]) -> list[dict]:
    """Group corrections by (field_name, new_value) and detect repeating patterns."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in corrections:
        key = (c["field_name"], c["new_value"])
        groups[key] = groups.get(key, [])
        groups[key].append(c)

    candidates = []
    for (field_name, new_value), group in groups.items():
        if len(group) < RULE_THRESHOLD:
            continue

        # Extract context from corrections
        descriptions = []
        amounts = []
        tins = []
        for c in group:
            ctx = c.get("context_data") or {}
            if ctx.get("description"):
                descriptions.append(ctx["description"])
            if ctx.get("amount"):
                amounts.append(ctx["amount"])
            if ctx.get("tin"):
                tins.append(ctx["tin"])

        # Determine rule type
        keywords = _extract_keywords(descriptions)
        rule_type = "keyword_override"
        match_criteria: dict[str, Any] = {}

        if keywords:
            match_criteria = {
                "field": "description",
                "operator": "contains_any",
                "value": keywords[:5],
            }
        elif tins and len(set(tins)) <= 3:
            rule_type = "supplier_default"
            match_criteria = {
                "field": "tin",
                "operator": "in",
                "value": list(set(tins)),
            }
        elif amounts:
            # Check if all amounts are above a threshold
            min_amount = min(amounts)
            max_amount = max(amounts)
            if min_amount > 0:
                rule_type = "amount_threshold"
                match_criteria = {
                    "field": "amount",
                    "operator": "between",
                    "value": [float(min_amount * 0.8), float(max_amount * 1.2)],
                }
            else:
                # Generic pattern — use old→new value mapping
                match_criteria = {
                    "field": field_name,
                    "operator": "was",
                    "value": list({c.get("old_value") for c in group if c.get("old_value")}),
                }

        confidence = min(0.95, 0.70 + len(group) * 0.05)

        candidates.append({
            "rule_type": rule_type,
            "match_criteria": match_criteria,
            "correction_field": field_name,
            "correction_value": new_value,
            "source_correction_count": len(group),
            "confidence": round(confidence, 2),
            "sample_descriptions": descriptions[:3],
        })

    return candidates


async def analyze_corrections(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[dict]:
    """Analyze all corrections for a tenant and return candidate rules.

    Returns list of candidate rule dicts (not yet persisted).
    """
    repo = CorrectionRepository(db)
    corrections_raw = await repo.find_by_tenant(tenant_id, limit=500)
    corrections = [
        {
            "field_name": c.field_name,
            "new_value": c.new_value,
            "old_value": c.old_value,
            "context_data": c.context_data,
            "entity_type": c.entity_type,
        }
        for c in corrections_raw
    ]

    candidates = _detect_patterns(corrections)
    logger.info(
        "Pattern analysis: %d corrections → %d candidate rules for tenant %s",
        len(corrections),
        len(candidates),
        tenant_id,
    )
    return candidates


async def persist_candidate_rules(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    candidates: list[dict],
) -> list[dict]:
    """Persist candidate rules (inactive by default, awaiting accountant review)."""
    rule_repo = CorrectionRuleRepository(db)
    persisted = []
    for cand in candidates:
        rule = await rule_repo.upsert(
            tenant_id=tenant_id,
            rule_type=cand["rule_type"],
            match_criteria=cand["match_criteria"],
            correction_field=cand["correction_field"],
            correction_value=cand["correction_value"],
            source_correction_count=cand["source_correction_count"],
            confidence=cand["confidence"],
        )
        persisted.append({
            "id": str(rule.id),
            "rule_type": rule.rule_type,
            "match_criteria": rule.match_criteria,
            "correction_field": rule.correction_field,
            "correction_value": rule.correction_value,
            "confidence": float(rule.confidence),
            "source_correction_count": rule.source_correction_count,
            "is_active": rule.is_active,
        })
    return persisted


async def get_learning_stats(
    db: AsyncSession, tenant_id: uuid.UUID
) -> dict:
    """Get learning system stats for a tenant."""
    correction_repo = CorrectionRepository(db)
    rule_repo = CorrectionRuleRepository(db)

    total_corrections = await correction_repo.count_by_tenant(tenant_id)
    all_rules = await rule_repo.find_by_tenant(tenant_id)
    active_rules = [r for r in all_rules if r.is_active]

    return {
        "total_corrections": total_corrections,
        "total_rules": len(all_rules),
        "active_rules": len(active_rules),
        "correction_stats": await correction_repo.get_correction_stats(tenant_id),
    }
