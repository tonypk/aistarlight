"""AI transaction classification: rule-based pre-classification + LLM batch classification.

Workflow: deterministic rules first → LLM for ambiguous items → confidence scoring.
"""

import json
import logging
import re
from typing import Any

from backend.core.llm import chat_completion

logger = logging.getLogger(__name__)

BATCH_SIZE = 25  # Transactions per LLM call

# Rule-based classification patterns
RULE_PATTERNS: list[dict[str, Any]] = [
    # Government payments (TIN patterns or keywords)
    {
        "match": lambda t: _is_government_entity(t.get("description", ""), t.get("tin")),
        "vat_type": "government",
        "category": "sale",
        "confidence": 0.95,
    },
    # Zero-rated exports
    {
        "match": lambda t: any(
            kw in (t.get("description", "") or "").lower()
            for kw in ["export", "foreign", "overseas", "international shipment"]
        ),
        "vat_type": "zero_rated",
        "category": "sale",
        "confidence": 0.85,
    },
    # VAT exempt items
    {
        "match": lambda t: any(
            kw in (t.get("description", "") or "").lower()
            for kw in [
                "agricultural", "senior citizen", "pwd discount",
                "educational", "cooperatives", "raw food",
            ]
        ),
        "vat_type": "exempt",
        "category": "goods",
        "confidence": 0.80,
    },
    # Professional services
    {
        "match": lambda t: any(
            kw in (t.get("description", "") or "").lower()
            for kw in [
                "consulting", "professional fee", "legal fee", "audit fee",
                "accounting", "advisory", "retainer",
            ]
        ),
        "vat_type": "vatable",
        "category": "services",
        "confidence": 0.90,
    },
    # Capital goods
    {
        "match": lambda t: any(
            kw in (t.get("description", "") or "").lower()
            for kw in [
                "equipment", "machinery", "vehicle", "computer",
                "furniture", "office renovation", "capital",
            ]
        ),
        "vat_type": "vatable",
        "category": "capital",
        "confidence": 0.85,
    },
    # Import-related
    {
        "match": lambda t: any(
            kw in (t.get("description", "") or "").lower()
            for kw in [
                "import", "customs", "brokerage", "freight",
                "shipping", "duty", "tariff",
            ]
        ),
        "vat_type": "vatable",
        "category": "imports",
        "confidence": 0.85,
    },
]

# Government TIN patterns (Philippines)
GOVT_TIN_PREFIXES = ["000", "001", "002"]

CLASSIFICATION_SYSTEM_PROMPT = """You are an expert Philippine tax accountant. Classify each transaction for BIR VAT filing.

For each transaction, determine:
1. vat_type: "vatable" | "exempt" | "zero_rated" | "government"
2. category: "goods" | "services" | "capital" | "imports" | "sale"
3. confidence: 0.00-1.00 (how confident you are)

Rules:
- Sales to government entities: vat_type="government", category="sale"
- Export sales: vat_type="zero_rated", category="sale"
- Regular domestic sales: vat_type="vatable", category="sale"
- Purchase of goods for resale: category="goods"
- Professional/service fees: category="services"
- Equipment/machinery: category="capital" (if amount > 1,000,000 PHP)
- Imported goods: category="imports"
- Agricultural/exempt items: vat_type="exempt"

Respond ONLY with valid JSON array:
[
  {"index": 0, "vat_type": "vatable", "category": "goods", "confidence": 0.90},
  ...
]
"""


def _is_government_entity(description: str, tin: str | None) -> bool:
    """Check if transaction involves a government entity."""
    desc_lower = (description or "").lower()
    govt_keywords = [
        "bir", "bureau of internal revenue", "government", "sss",
        "philhealth", "pag-ibig", "hdmf", "lgu", "municipality",
        "national government", "dti", "sec registration",
    ]
    if any(kw in desc_lower for kw in govt_keywords):
        return True
    if tin:
        tin_clean = re.sub(r"[^0-9]", "", tin)
        if any(tin_clean.startswith(p) for p in GOVT_TIN_PREFIXES):
            return True
    return False


def apply_rule_based_classification(transaction: dict) -> dict | None:
    """Try to classify a transaction using deterministic rules.

    Returns classification dict or None if no rule matches.
    """
    for rule in RULE_PATTERNS:
        if rule["match"](transaction):
            return {
                "vat_type": rule["vat_type"],
                "category": rule["category"],
                "confidence": rule["confidence"],
                "classification_source": "rule",
            }
    return None


async def classify_batch(
    transactions: list[dict], tenant_context: dict | None = None
) -> list[dict]:
    """Classify a batch of transactions using LLM.

    Args:
        transactions: List of {index, date, description, amount, tin} dicts.
        tenant_context: Optional context like industry, common vendors etc.

    Returns list of {index, vat_type, category, confidence} dicts.
    """
    if not transactions:
        return []

    # Build concise transaction descriptions for LLM
    items = []
    for t in transactions:
        items.append({
            "index": t["index"],
            "date": t.get("date"),
            "description": t.get("description", "")[:200],  # Truncate long descriptions
            "amount": t.get("amount", 0),
            "tin": t.get("tin"),
        })

    context_parts = [f"Classify these {len(items)} transactions:"]
    if tenant_context:
        if tenant_context.get("industry"):
            context_parts.append(f"Business industry: {tenant_context['industry']}")
        if tenant_context.get("vat_classification"):
            context_parts.append(f"VAT classification: {tenant_context['vat_classification']}")

    context_parts.append(json.dumps(items, default=str))

    try:
        response = await chat_completion(
            messages=[{"role": "user", "content": "\n".join(context_parts)}],
            system=CLASSIFICATION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=2048,
        )

        # Parse JSON response
        start = response.index("[")
        end = response.rindex("]") + 1
        results = json.loads(response[start:end])

        # Validate and normalize results
        valid_vat_types = {"vatable", "exempt", "zero_rated", "government"}
        valid_categories = {"goods", "services", "capital", "imports", "sale"}

        for r in results:
            if r.get("vat_type") not in valid_vat_types:
                r["vat_type"] = "vatable"
            if r.get("category") not in valid_categories:
                r["category"] = "goods"
            r["confidence"] = max(0.0, min(1.0, float(r.get("confidence", 0.5))))

        return results

    except (ValueError, json.JSONDecodeError, KeyError) as e:
        logger.warning("LLM classification failed: %s", e)
        # Return default classification for all items
        return [
            {
                "index": t["index"],
                "vat_type": "vatable",
                "category": "goods",
                "confidence": 0.30,
            }
            for t in transactions
        ]


async def classify_transactions(
    transactions: list[dict], tenant_context: dict | None = None
) -> list[dict]:
    """Classify all transactions: rules first, then LLM for the rest.

    Args:
        transactions: List of transaction dicts with date, description, amount, tin.
        tenant_context: Optional tenant context for LLM.

    Returns list of dicts with added vat_type, category, confidence, classification_source.
    """
    results = [None] * len(transactions)
    needs_llm = []

    # Phase 1: Rule-based classification
    for i, txn in enumerate(transactions):
        rule_result = apply_rule_based_classification(txn)
        if rule_result:
            results[i] = {**txn, **rule_result}
        else:
            needs_llm.append({"index": i, **txn})

    # Phase 2: LLM batch classification for remaining
    if needs_llm:
        for batch_start in range(0, len(needs_llm), BATCH_SIZE):
            batch = needs_llm[batch_start : batch_start + BATCH_SIZE]
            llm_results = await classify_batch(batch, tenant_context)

            # Build lookup by index
            llm_lookup = {r["index"]: r for r in llm_results}

            for item in batch:
                idx = item["index"]
                llm_cls = llm_lookup.get(idx, {})
                results[idx] = {
                    **transactions[idx],
                    "vat_type": llm_cls.get("vat_type", "vatable"),
                    "category": llm_cls.get("category", "goods"),
                    "confidence": llm_cls.get("confidence", 0.30),
                    "classification_source": "ai",
                }

    # Fill any remaining None entries (shouldn't happen, but safety)
    for i, r in enumerate(results):
        if r is None:
            results[i] = {
                **transactions[i],
                "vat_type": "vatable",
                "category": "goods",
                "confidence": 0.0,
                "classification_source": "ai",
            }

    return results


async def reclassify_transaction(
    transaction: dict, user_hint: str | None = None
) -> dict:
    """Reclassify a single transaction, optionally with a user hint.

    Returns classification dict.
    """
    context = f"Reclassify this transaction: {json.dumps(transaction, default=str)}"
    if user_hint:
        context += f"\nUser hint: {user_hint}"

    try:
        response = await chat_completion(
            messages=[{"role": "user", "content": context}],
            system=CLASSIFICATION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=512,
        )
        start = response.index("[")
        end = response.rindex("]") + 1
        results = json.loads(response[start:end])
        if results:
            r = results[0]
            return {
                "vat_type": r.get("vat_type", "vatable"),
                "category": r.get("category", "goods"),
                "confidence": max(0.0, min(1.0, float(r.get("confidence", 0.5)))),
                "classification_source": "ai",
            }
    except (ValueError, json.JSONDecodeError, KeyError):
        pass

    return {
        "vat_type": "vatable",
        "category": "goods",
        "confidence": 0.30,
        "classification_source": "ai",
    }
