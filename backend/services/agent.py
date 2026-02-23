"""LLM Agent orchestration: routes user requests to appropriate services."""

import json
from typing import Any

from backend.core.llm import chat_completion_with_tools

AGENT_SYSTEM_PROMPT = """You are AIStarlight, an AI-powered Philippine tax filing assistant.
You help small and medium businesses with their BIR tax filings.

Your capabilities:
1. Process uploaded financial data (sales/purchase records)
2. Calculate VAT and generate BIR 2550M reports
3. Remember user preferences for recurring filings
4. Answer questions about Philippine tax regulations

Currently supported BIR forms:
- BIR 2550M (Monthly VAT Declaration) - fully supported
- BIR 2550Q, 1701, 1702, 2316, 1601C, SAWT - planned

When the user asks to generate a report, use the generate_report tool.
When the user asks about tax rules, answer from your knowledge.
When the user uploads data, guide them through the mapping process.

Always respond in a professional but friendly manner.
Use the language the user writes in (English or Filipino).
"""

AGENT_TOOLS = [
    {
        "name": "generate_report",
        "description": "Generate a BIR tax report for a specific period",
        "input_schema": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "description": "BIR form type, e.g., BIR_2550M",
                },
                "period": {
                    "type": "string",
                    "description": "Filing period, e.g., 2026-01",
                },
            },
            "required": ["report_type", "period"],
        },
    },
    {
        "name": "lookup_tax_rule",
        "description": "Look up a Philippine tax regulation or rule",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The tax question or topic to look up",
                },
                "category": {
                    "type": "string",
                    "description": "Category: vat, income_tax, withholding, general",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_user_preferences",
        "description": "Retrieve saved user preferences for a report type",
        "input_schema": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "description": "The report type to get preferences for",
                },
            },
            "required": ["report_type"],
        },
    },
]


async def process_message(
    user_message: str,
    conversation_history: list[dict],
    tenant_context: dict[str, Any],
) -> dict[str, Any]:
    """Process a user message through the agent, returning response and any tool calls."""
    messages = [*conversation_history, {"role": "user", "content": user_message}]

    response = await chat_completion_with_tools(
        messages=messages,
        tools=AGENT_TOOLS,
        system=AGENT_SYSTEM_PROMPT,
    )

    # Check if agent wants to use tools
    tool_calls = []
    text_response = ""

    for block in response.content:
        if block.type == "text":
            text_response += block.text
        elif block.type == "tool_use":
            tool_calls.append({
                "tool_name": block.name,
                "tool_input": block.input,
                "tool_id": block.id,
            })

    return {
        "response": text_response,
        "tool_calls": tool_calls,
        "stop_reason": response.stop_reason,
    }
