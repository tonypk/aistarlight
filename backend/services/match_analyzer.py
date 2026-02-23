"""AI-powered match analysis for bank reconciliation.

Uses GPT-4.1 mini to suggest fuzzy matches for unmatched entries
and explain why entries don't match.
"""

import json
import logging
from dataclasses import asdict, dataclass

from backend.config import settings
from backend.core.llm import chat_completion

logger = logging.getLogger(__name__)

BATCH_SIZE = 10


@dataclass(frozen=True)
class MatchSuggestion:
    """AI-generated suggestion for a potential match."""

    unmatched_entry_index: int
    suggested_record_id: str | None
    confidence: float
    explanation: str
    category: str  # likely_match | possible_match | no_match | internal_transfer | bank_fee


@dataclass(frozen=True)
class MismatchExplanation:
    """AI-generated explanation for why an entry is unmatched."""

    entry_index: int
    entry_type: str  # bank | record
    mismatch_type: str  # amount_diff | date_diff | no_counterpart | fee | transfer
    explanation: str
    recommended_action: str  # review | create_receipt | ignore | investigate


SYSTEM_PROMPT = """You are a financial reconciliation assistant. You help match bank transactions
with accounting records and explain discrepancies.

Given unmatched bank entries and unmatched accounting records, you should:
1. Suggest potential matches (fuzzy matching by amount, date, description)
2. Identify entries that are likely bank fees, internal transfers, or timing differences
3. Explain why entries might not match

Respond in JSON format with two arrays:
{
  "suggestions": [
    {
      "unmatched_entry_index": 0,
      "suggested_record_id": "uuid-or-null",
      "confidence": 0.85,
      "explanation": "Amount matches within PHP 0.50, dates 2 days apart",
      "category": "likely_match"
    }
  ],
  "explanations": [
    {
      "entry_index": 0,
      "entry_type": "bank",
      "mismatch_type": "fee",
      "explanation": "This appears to be a bank service charge",
      "recommended_action": "ignore"
    }
  ]
}

Categories for suggestions: likely_match, possible_match, no_match, internal_transfer, bank_fee
Mismatch types: amount_diff, date_diff, no_counterpart, fee, transfer
Recommended actions: review, create_receipt, ignore, investigate"""


def _format_entries(entries: list[dict], label: str) -> str:
    """Format entries for the LLM prompt."""
    if not entries:
        return f"No unmatched {label} entries."

    lines = [f"Unmatched {label} entries:"]
    for i, entry in enumerate(entries):
        amount = entry.get("amount", 0)
        date = entry.get("date", "N/A")
        desc = (entry.get("description") or "")[:80]
        entry_id = entry.get("id", f"idx-{i}")
        lines.append(f"  [{i}] id={entry_id}, date={date}, amount={amount}, desc=\"{desc}\"")
    return "\n".join(lines)


def _format_all_records(records: list[dict], label: str) -> str:
    """Format all records as potential match candidates."""
    if not records:
        return f"No {label} available for matching."

    lines = [f"All {label} (potential match candidates):"]
    for entry in records[:50]:  # Limit context size
        amount = entry.get("amount", 0)
        date = entry.get("date", "N/A")
        desc = (entry.get("description") or "")[:60]
        entry_id = entry.get("id", "?")
        lines.append(f"  id={entry_id}, date={date}, amount={amount}, desc=\"{desc}\"")
    return "\n".join(lines)


def _parse_ai_response(
    response_text: str,
    bank_offset: int,
    record_offset: int,
) -> tuple[list[MatchSuggestion], list[MismatchExplanation]]:
    """Parse AI response JSON into typed dataclasses."""
    suggestions: list[MatchSuggestion] = []
    explanations: list[MismatchExplanation] = []

    # Extract JSON from response (handle markdown code blocks)
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse AI response as JSON: %s", text[:200])
        return suggestions, explanations

    for s in data.get("suggestions", []):
        try:
            suggestions.append(MatchSuggestion(
                unmatched_entry_index=int(s.get("unmatched_entry_index", 0)) + bank_offset,
                suggested_record_id=s.get("suggested_record_id"),
                confidence=float(s.get("confidence", 0)),
                explanation=str(s.get("explanation", "")),
                category=str(s.get("category", "no_match")),
            ))
        except (ValueError, TypeError) as e:
            logger.debug("Skipping invalid suggestion: %s", e)

    for e in data.get("explanations", []):
        try:
            explanations.append(MismatchExplanation(
                entry_index=int(e.get("entry_index", 0)) + (
                    bank_offset if e.get("entry_type") == "bank" else record_offset
                ),
                entry_type=str(e.get("entry_type", "bank")),
                mismatch_type=str(e.get("mismatch_type", "no_counterpart")),
                explanation=str(e.get("explanation", "")),
                recommended_action=str(e.get("recommended_action", "review")),
            ))
        except (ValueError, TypeError) as e_err:
            logger.debug("Skipping invalid explanation: %s", e_err)

    return suggestions, explanations


async def analyze_unmatched_entries(
    unmatched_bank: list[dict],
    unmatched_records: list[dict],
    all_records: list[dict],
    all_bank: list[dict],
    max_suggestions: int = 20,
) -> tuple[list[MatchSuggestion], list[MismatchExplanation]]:
    """Use GPT-4.1 mini to analyze unmatched entries in batches.

    Args:
        unmatched_bank: Bank entries that didn't match any record.
        unmatched_records: Accounting records that didn't match any bank entry.
        all_records: All accounting records (for context).
        all_bank: All bank entries (for context).
        max_suggestions: Maximum total suggestions to return.

    Returns:
        Tuple of (suggestions, explanations).
    """
    all_suggestions: list[MatchSuggestion] = []
    all_explanations: list[MismatchExplanation] = []

    model = getattr(settings, "match_analyzer_model", None) or "gpt-4.1-mini"

    # Process unmatched bank entries in batches
    for batch_start in range(0, len(unmatched_bank), BATCH_SIZE):
        if len(all_suggestions) >= max_suggestions:
            break

        batch = unmatched_bank[batch_start : batch_start + BATCH_SIZE]

        prompt = (
            f"{_format_entries(batch, 'bank')}\n\n"
            f"{_format_all_records(all_records, 'accounting records')}\n\n"
            "Analyze these unmatched bank entries. Suggest possible matches from "
            "the accounting records and explain why entries might not have matched."
        )

        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system=SYSTEM_PROMPT,
                model=model,
                max_tokens=2048,
                temperature=0.2,
            )
            sug, exp = _parse_ai_response(response, batch_start, 0)
            all_suggestions.extend(sug)
            all_explanations.extend(exp)
        except Exception as e:
            logger.error("AI analysis failed for bank batch %d: %s", batch_start, e)

    # Process unmatched records in batches
    for batch_start in range(0, len(unmatched_records), BATCH_SIZE):
        if len(all_suggestions) >= max_suggestions:
            break

        batch = unmatched_records[batch_start : batch_start + BATCH_SIZE]

        prompt = (
            f"{_format_entries(batch, 'accounting record')}\n\n"
            f"{_format_all_records(all_bank, 'bank entries')}\n\n"
            "Analyze these unmatched accounting records. Suggest possible matches from "
            "the bank entries and explain why they might not have matched."
        )

        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system=SYSTEM_PROMPT,
                model=model,
                max_tokens=2048,
                temperature=0.2,
            )
            sug, exp = _parse_ai_response(response, 0, batch_start)
            all_suggestions.extend(sug)
            all_explanations.extend(exp)
        except Exception as e:
            logger.error("AI analysis failed for record batch %d: %s", batch_start, e)

    # Trim to max
    return all_suggestions[:max_suggestions], all_explanations
