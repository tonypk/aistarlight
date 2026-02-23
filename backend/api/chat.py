from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.knowledge import KnowledgeChunk
from backend.models.tenant import User
from backend.schemas.chat import ChatMessageRequest
from backend.schemas.common import ok
from backend.services.agent import process_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
async def send_message(
    data: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Send a message to the AI tax assistant."""
    # Build conversation context
    from backend.models.memory import CorrectionHistory

    # Load recent chat messages for context
    from sqlalchemy import desc

    # For MVP, we pass in an empty history;
    # full chat persistence will be in a later phase
    conversation_history: list[dict] = []

    tenant_context = {
        "tenant_id": str(user.tenant_id),
        "user_name": user.full_name,
    }

    result = await process_message(
        user_message=data.content,
        conversation_history=conversation_history,
        tenant_context=tenant_context,
    )

    return ok({
        "role": "assistant",
        "content": result["response"],
        "tool_calls": result.get("tool_calls", []),
    })


@router.get("/history")
async def get_history(
    page: int = 1,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get chat history (placeholder for MVP)."""
    # Chat persistence will be implemented in phase 5
    return ok([], meta={"total": 0, "page": page, "limit": limit})
