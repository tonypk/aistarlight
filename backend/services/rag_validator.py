"""RAG-based compliance validator — uses knowledge base + LLM to validate reports.

Complements the deterministic rule engine with AI-powered regulation checking.
"""

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.llm import chat_completion
from backend.services.knowledge_retriever import retrieve_relevant_knowledge

logger = logging.getLogger(__name__)

RAG_VALIDATION_PROMPT = """You are an expert Philippine BIR tax compliance auditor.

Given the following tax report data and relevant BIR regulations, identify any compliance issues.

For each finding, provide:
1. finding: Clear description of the issue
2. severity: "high" | "medium" | "low"
3. regulation_reference: The specific BIR regulation, revenue regulation, or circular

Focus on:
- Correct application of tax rates
- Proper categorization of income/expenses
- Compliance with filing requirements
- Any regulatory changes that may affect this filing

Respond ONLY with a valid JSON array:
[
  {"finding": "...", "severity": "high", "regulation_reference": "RR 16-2005 Section 4.112-1"},
  ...
]

If no issues found, return an empty array: []
"""


async def validate_with_rag(
    report_data: dict[str, Any],
    report_type: str,
    db: AsyncSession,
) -> list[dict]:
    """Validate a report using RAG knowledge + LLM analysis.

    Returns list of findings: [{finding, severity, regulation_reference}]
    """
    query = f"BIR {report_type.replace('BIR_', '')} compliance requirements filing rules"
    knowledge_chunks = await retrieve_relevant_knowledge(
        query=query,
        category="bir_regulations",
        db=db,
        limit=5,
    )

    if not knowledge_chunks:
        # Try broader search
        knowledge_chunks = await retrieve_relevant_knowledge(
            query="Philippine VAT withholding tax compliance",
            db=db,
            limit=3,
        )

    context = "\n\n".join(
        f"[{c['source']}]: {c['content']}" for c in knowledge_chunks
    ) if knowledge_chunks else "No specific regulations found in knowledge base."

    # Build concise report summary for LLM
    report_summary = {
        "report_type": report_type,
        "period": report_data.get("period", ""),
    }
    for key, value in report_data.items():
        if key.startswith("line_") or key in ("period", "total_sales", "net_vat_payable"):
            report_summary[key] = value

    user_msg = (
        f"## Regulations Context\n{context}\n\n"
        f"## Report Data\n{json.dumps(report_summary, default=str, indent=2)}"
    )

    try:
        response = await chat_completion(
            messages=[{"role": "user", "content": user_msg}],
            system=RAG_VALIDATION_PROMPT,
            temperature=0.1,
            max_tokens=2048,
        )
        start = response.index("[")
        end = response.rindex("]") + 1
        findings = json.loads(response[start:end])

        # Validate structure
        valid_severities = {"high", "medium", "low"}
        validated = []
        for f in findings:
            if isinstance(f, dict) and "finding" in f:
                validated.append({
                    "finding": str(f["finding"])[:500],
                    "severity": f.get("severity", "medium") if f.get("severity") in valid_severities else "medium",
                    "regulation_reference": str(f.get("regulation_reference", ""))[:200],
                })
        return validated

    except (ValueError, json.JSONDecodeError, KeyError) as e:
        logger.warning("RAG validation failed to parse response: %s", e)
        return []
    except Exception as e:
        logger.error("RAG validation error: %s", e)
        return []
