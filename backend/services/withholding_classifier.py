"""Withholding tax classification service.

Two-phase classification (same pattern as classifier_service.py):
1. Rule-based: keyword matching against ATC codes + supplier defaults
2. LLM-based: for ambiguous transactions
"""

import json
import logging
from decimal import Decimal
from typing import Any

from backend.core.llm import chat_completion
from backend.services.ewt_rates import EWT_RATES, find_atc_by_keywords, get_rate

logger = logging.getLogger(__name__)

BATCH_SIZE = 25

# Transactions exempt from EWT
EWT_EXEMPT_KEYWORDS = [
    "salary", "wages", "payroll",
    "government", "bir", "sss", "philhealth", "pag-ibig",
    "utility", "electric bill", "water bill", "internet bill",
    "bank charge", "bank fee", "interest expense",
]

EWT_CLASSIFICATION_PROMPT = """You are an expert Philippine tax accountant specializing in Expanded Withholding Tax (EWT).

For each purchase transaction, determine if EWT applies and classify it:

1. ewt_applicable: true/false - Does EWT apply to this transaction?
2. atc_code: The ATC code (e.g., "WC010", "WI050", "WC120")
3. ewt_rate: The withholding rate (e.g., 0.02 for 2%, 0.05 for 5%, 0.10 for 10%)
4. income_type: Brief description of income type
5. confidence: 0.00-1.00

EWT Rules:
- Professional fees (individual <3M): WI010 at 5%
- Professional fees (individual >=3M): WI020 at 10%
- Professional fees (corporation): WC010 at 10%
- Rent (real property): WI030 at 5%
- Contractors/Subcontractors: WI050/WC050 at 2%
- Advertising/Promotions: WC060 at 2%
- Commission/Brokerage: WI070/WC070 at 10%
- Purchase of goods (>3M annual): WI100/WC100 at 1%
- Service payments: WI120/WC120 at 2%
- Transport/Delivery: WI150 at 2%
- Toll fees: WI160 at 1%

EWT does NOT apply to:
- Salaries/wages (use withholding tax on compensation instead)
- Government payments
- Bank charges, utility bills
- Purchases below PHP 10,000 (generally)

Respond ONLY with valid JSON array:
[
  {"index": 0, "ewt_applicable": true, "atc_code": "WC010", "ewt_rate": 0.10, "income_type": "Professional fees", "confidence": 0.85},
  ...
]
"""


def classify_ewt_rule_based(
    transaction: dict,
    supplier_info: dict | None = None,
) -> dict | None:
    """Try to classify a transaction's EWT using deterministic rules.

    Returns classification dict or None if no rule matches.
    """
    desc = (transaction.get("description") or "").lower()

    # Check if exempt from EWT
    if any(kw in desc for kw in EWT_EXEMPT_KEYWORDS):
        return {
            "ewt_applicable": False,
            "atc_code": None,
            "ewt_rate": None,
            "income_type": None,
            "confidence": 0.90,
            "classification_source": "rule",
        }

    # Use supplier defaults if available
    if supplier_info and supplier_info.get("default_atc_code"):
        atc = supplier_info["default_atc_code"]
        rate = float(get_rate(atc))
        return {
            "ewt_applicable": True,
            "atc_code": atc,
            "ewt_rate": rate,
            "income_type": EWT_RATES[atc]["desc"],
            "confidence": 0.85,
            "classification_source": "rule",
        }

    # Try keyword matching
    supplier_type = "corporation"
    if supplier_info:
        supplier_type = supplier_info.get("supplier_type", "corporation")

    atc = find_atc_by_keywords(desc, supplier_type)
    if atc:
        rate = float(get_rate(atc))
        return {
            "ewt_applicable": True,
            "atc_code": atc,
            "ewt_rate": rate,
            "income_type": EWT_RATES[atc]["desc"],
            "confidence": 0.75,
            "classification_source": "rule",
        }

    return None


async def classify_ewt_batch(
    transactions: list[dict],
    tenant_context: dict | None = None,
) -> list[dict]:
    """Classify a batch of transactions using LLM for EWT applicability.

    Args:
        transactions: List of {index, description, amount, supplier_type} dicts.
        tenant_context: Optional context.

    Returns:
        List of classification results.
    """
    prompt_lines = ["Classify these purchase transactions for EWT:\n"]
    for i, t in enumerate(transactions):
        prompt_lines.append(
            f"{i}. Description: {t.get('description', 'N/A')} | "
            f"Amount: {t.get('amount', 0)} PHP | "
            f"Supplier Type: {t.get('supplier_type', 'corporation')}"
        )

    user_message = "\n".join(prompt_lines)

    try:
        response = await chat_completion(
            messages=[
                {"role": "system", "content": EWT_CLASSIFICATION_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        content = response.strip()
        # Extract JSON from response
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        results = json.loads(content)

        # Map results back to transaction order
        result_map = {r["index"]: r for r in results}
        classified = []
        for i in range(len(transactions)):
            r = result_map.get(i, {})
            classified.append({
                "ewt_applicable": r.get("ewt_applicable", False),
                "atc_code": r.get("atc_code"),
                "ewt_rate": r.get("ewt_rate"),
                "income_type": r.get("income_type"),
                "confidence": r.get("confidence", 0.5),
                "classification_source": "ai",
            })
        return classified
    except Exception as e:
        logger.error("EWT batch classification failed: %s", e)
        return [
            {
                "ewt_applicable": False,
                "atc_code": None,
                "ewt_rate": None,
                "income_type": None,
                "confidence": 0.3,
                "classification_source": "ai",
            }
            for _ in transactions
        ]


async def classify_ewt_transactions(
    transactions: list[dict],
    supplier_lookup: dict[str, dict] | None = None,
    tenant_context: dict | None = None,
    tenant_id=None,
    db=None,
) -> list[dict]:
    """Classify transactions for EWT applicability using rule+learned+LLM approach.

    Args:
        transactions: List of transaction dicts with description, amount, tin, etc.
        supplier_lookup: Optional {tin: supplier_info} for supplier defaults.
        tenant_context: Optional tenant context.
        tenant_id: Optional tenant UUID for learned rules.
        db: Optional AsyncSession for DB access.

    Returns:
        List of classification results, same length as transactions.
    """
    results: list[dict | None] = [None] * len(transactions)
    unclassified_indices: list[int] = []

    # Phase 1: Rule-based classification
    for i, txn in enumerate(transactions):
        supplier_info = None
        if supplier_lookup and txn.get("tin"):
            supplier_info = supplier_lookup.get(txn["tin"])

        result = classify_ewt_rule_based(txn, supplier_info)
        if result:
            results[i] = result
        else:
            unclassified_indices.append(i)

    # Phase 1.5: Learned rules from corrections
    still_unclassified = []
    if tenant_id and db and unclassified_indices:
        try:
            from backend.repositories.correction_rule_repo import CorrectionRuleRepository
            from backend.services.classifier_service import _apply_learned_rule
            rule_repo = CorrectionRuleRepository(db)
            learned_rules = await rule_repo.find_active(tenant_id)
            for i in unclassified_indices:
                txn = transactions[i]
                matched = False
                for rule in learned_rules:
                    if rule.correction_field in ("atc_code", "ewt_rate", "ewt_applicable"):
                        lr = _apply_learned_rule(txn, rule)
                        if lr:
                            results[i] = {
                                "ewt_applicable": True,
                                "atc_code": lr.get("atc_code"),
                                "ewt_rate": lr.get("ewt_rate"),
                                "income_type": None,
                                "confidence": lr.get("confidence", 0.85),
                                "classification_source": "learned",
                            }
                            matched = True
                            break
                if not matched:
                    still_unclassified.append(i)
        except Exception as e:
            logger.warning("Failed to load learned rules for EWT: %s", e)
            still_unclassified = list(unclassified_indices)
    else:
        still_unclassified = list(unclassified_indices)

    logger.info(
        "EWT classification: %d rule, %d learned, %d remaining for LLM",
        len(transactions) - len(unclassified_indices),
        len(unclassified_indices) - len(still_unclassified),
        len(still_unclassified),
    )

    unclassified_indices = still_unclassified

    # Phase 2: LLM classification for remaining
    if unclassified_indices:
        for batch_start in range(0, len(unclassified_indices), BATCH_SIZE):
            batch_indices = unclassified_indices[batch_start : batch_start + BATCH_SIZE]
            batch_txns = [
                {
                    "index": j,
                    "description": transactions[idx].get("description"),
                    "amount": transactions[idx].get("amount", 0),
                    "supplier_type": (
                        supplier_lookup.get(transactions[idx].get("tin", ""), {}).get(
                            "supplier_type", "corporation"
                        )
                        if supplier_lookup
                        else "corporation"
                    ),
                }
                for j, idx in enumerate(batch_indices)
            ]
            batch_results = await classify_ewt_batch(batch_txns, tenant_context)
            for j, idx in enumerate(batch_indices):
                if j < len(batch_results):
                    results[idx] = batch_results[j]

    # Fill any remaining None with defaults
    for i in range(len(results)):
        if results[i] is None:
            results[i] = {
                "ewt_applicable": False,
                "atc_code": None,
                "ewt_rate": None,
                "income_type": None,
                "confidence": 0.3,
                "classification_source": "ai",
            }

    return results
