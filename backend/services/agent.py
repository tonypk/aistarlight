"""LLM Agent orchestration: routes user requests to appropriate services."""

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.llm import chat_completion_stream, chat_completion_with_tools

AGENT_SYSTEM_PROMPT = """You are AIStarlight, an AI-powered Philippine tax filing assistant.
You help small and medium businesses with their BIR tax filings.

Your capabilities:
1. Process uploaded financial data (sales/purchase records, bank statements, receipts)
2. Calculate VAT, withholding tax, and generate BIR reports
3. AI-powered transaction classification and column mapping
4. Bank & billing auto-reconciliation (CSV/Excel/PDF/image, supports BDO/BPI/Metrobank/PayPal/Stripe/GCash)
5. Receipt OCR scanning and data extraction
6. EWT classification, BIR 2307 certificate generation, and SAWT
7. Compliance validation and anomaly detection
8. Remember user preferences for recurring filings
9. Answer questions about Philippine tax regulations (289 knowledge entries covering VAT, income tax, withholding, payroll, incentives, compliance)

Currently supported BIR forms:
- BIR 2550M (Monthly VAT Declaration) - fully supported
- BIR 2550Q (Quarterly VAT Return) - fully supported
- BIR 1601-C (Monthly Withholding Tax on Compensation) - fully supported
- BIR 0619-E (Monthly Expanded Withholding Tax) - fully supported
- BIR 2307 (Certificate of Creditable Tax Withheld) - fully supported (PDF generation)
- SAWT (Summary Alphalist of Withholding Taxes) - fully supported (CSV/PDF)
- BIR 1701, 1702, 2316 - coming soon

When the user asks to generate a report, use the generate_report tool.
When the user asks about tax rules, use the lookup_tax_rule tool.
When the user asks about their settings or preferences, use the get_user_preferences tool.

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
                    "description": "BIR form type: BIR_2550M, BIR_2550Q, BIR_1601C, BIR_0619E",
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
                    "description": "Category: vat, income_tax, withholding, compliance, general, payroll, incentives",
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


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> str:
    """Execute a tool call and return the result as a string."""
    if tool_name == "generate_report":
        return await _execute_generate_report(tool_input, tenant_id, db)
    elif tool_name == "lookup_tax_rule":
        return await _execute_lookup_tax_rule(tool_input, db)
    elif tool_name == "get_user_preferences":
        return await _execute_get_preferences(tool_input, tenant_id, db)
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


async def _execute_generate_report(
    tool_input: dict,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> str:
    """Guide user to the upload flow for report generation."""
    report_type = tool_input.get("report_type", "BIR_2550M")
    period = tool_input.get("period", "")

    supported_types = {"BIR_2550M", "BIR_2550Q", "BIR_1601C", "BIR_0619E"}
    if report_type not in supported_types:
        return json.dumps({"error": f"Report type {report_type} not yet supported. Supported: {', '.join(sorted(supported_types))}"})

    # Check if user has existing reports for this period
    from backend.repositories.report import ReportRepository

    repo = ReportRepository(db)
    existing = await repo.find_by_tenant(tenant_id, offset=0, limit=100)
    matching = [r for r in existing if r.period == period and r.report_type == report_type]

    if matching:
        report = matching[0]
        return json.dumps({
            "existing_report_id": str(report.id),
            "status": report.status,
            "message": f"You already have a {report_type} report for {period} (status: {report.status}). "
            "You can view it in the Reports page. To create a new one, go to Upload Data → Column Mapping → Generate Report.",
        })

    return json.dumps({
        "action": "guide_to_upload",
        "report_type": report_type,
        "period": period,
        "message": f"To generate a {report_type} report for {period}, please follow these steps:\n"
        "1. Go to **Upload Data** and upload your sales/purchase CSV or Excel file\n"
        "2. The system will auto-detect your columns and suggest mappings\n"
        "3. Confirm the column mappings\n"
        "4. Select the period and generate the report\n\n"
        "This ensures your report has accurate data from your actual records.",
    })


async def _execute_lookup_tax_rule(
    tool_input: dict,
    db: AsyncSession,
) -> str:
    """Look up tax rules from knowledge base."""
    from backend.services.knowledge_retriever import retrieve_relevant_knowledge

    query = tool_input.get("query", "")
    category = tool_input.get("category")

    chunks = await retrieve_relevant_knowledge(query, category=category, db=db, limit=3)

    if not chunks:
        return json.dumps({
            "answer": "No specific regulation found in our knowledge base for this query. "
            "Please consult the BIR website (www.bir.gov.ph) for the latest regulations.",
            "sources": [],
        })

    return json.dumps({
        "answer": "\n\n".join(c["content"] for c in chunks),
        "sources": [c["source"] for c in chunks if c.get("source")],
    })


async def _execute_get_preferences(
    tool_input: dict,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> str:
    """Get user preferences for a report type."""
    from backend.services.memory_manager import get_preference

    report_type = tool_input.get("report_type", "BIR_2550M")
    pref = await get_preference(tenant_id, report_type, db)

    if not pref:
        return json.dumps({"message": f"No saved preferences for {report_type}"})

    return json.dumps({
        "report_type": pref["report_type"],
        "column_mappings": pref["column_mappings"],
        "format_rules": pref["format_rules"],
    })


async def process_message(
    user_message: str,
    conversation_history: list[dict],
    tenant_context: dict[str, Any],
    db: AsyncSession | None = None,
) -> dict[str, Any]:
    """Process a user message through the agent, executing any tool calls.

    Returns response dict with 'response' and 'tool_calls' keys.
    """
    messages = [*conversation_history, {"role": "user", "content": user_message}]

    response = await chat_completion_with_tools(
        messages=messages,
        tools=AGENT_TOOLS,
        system=AGENT_SYSTEM_PROMPT,
    )

    choice = response.choices[0]
    tool_calls_executed = []

    # If the model wants to call tools, execute them and make a follow-up call
    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        # Serialize the assistant message with tool calls into a plain dict
        assistant_message = {
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in choice.message.tool_calls
            ],
        }
        follow_up_messages = [*messages, assistant_message]

        for tc in choice.message.tool_calls:
            tool_name = tc.function.name
            tool_input = json.loads(tc.function.arguments)

            # Execute the tool
            if db is not None:
                tenant_id = uuid.UUID(tenant_context.get("tenant_id", ""))
                tool_result = await execute_tool(tool_name, tool_input, tenant_id, db)
            else:
                tool_result = json.dumps({"error": "Database session not available"})

            tool_calls_executed.append({
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_id": tc.id,
                "result": tool_result,
            })

            # Add tool result message
            follow_up_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

        # Make follow-up LLM call with tool results
        follow_up_response = await chat_completion_with_tools(
            messages=follow_up_messages,
            tools=AGENT_TOOLS,
            system=AGENT_SYSTEM_PROMPT,
        )
        text_response = follow_up_response.choices[0].message.content or ""
    else:
        text_response = choice.message.content or ""

    return {
        "response": text_response,
        "tool_calls": tool_calls_executed,
        "stop_reason": choice.finish_reason,
    }


async def process_message_stream(
    user_message: str,
    conversation_history: list[dict],
    tenant_context: dict[str, Any],
    db: AsyncSession | None = None,
) -> AsyncIterator[str]:
    """Process a user message through the agent, streaming the final response.

    Tool calls are executed non-streaming first.
    The final LLM response (with or without tool context) is streamed.
    """
    messages = [*conversation_history, {"role": "user", "content": user_message}]

    # First call: non-streaming to detect tool calls
    response = await chat_completion_with_tools(
        messages=messages,
        tools=AGENT_TOOLS,
        system=AGENT_SYSTEM_PROMPT,
    )

    choice = response.choices[0]

    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        # Execute tools
        assistant_message = {
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in choice.message.tool_calls
            ],
        }
        follow_up_messages = [*messages, assistant_message]

        for tc in choice.message.tool_calls:
            tool_name = tc.function.name
            tool_input = json.loads(tc.function.arguments)

            if db is not None:
                tenant_id = uuid.UUID(tenant_context.get("tenant_id", ""))
                tool_result = await execute_tool(tool_name, tool_input, tenant_id, db)
            else:
                tool_result = json.dumps({"error": "Database session not available"})

            follow_up_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

        # Stream the follow-up response
        async for token in chat_completion_stream(
            messages=follow_up_messages,
            system=AGENT_SYSTEM_PROMPT,
        ):
            yield token
    else:
        # No tool calls — yield the already-received response
        text = choice.message.content or ""
        if text:
            yield text
