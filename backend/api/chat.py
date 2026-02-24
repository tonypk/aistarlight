import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.tenant import User
from backend.repositories.chat import ChatMessageRepository
from backend.schemas.chat import ChatMessageRequest
from backend.schemas.common import ok
from backend.services.agent import process_message, process_message_stream

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
async def send_message(
    data: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Send a message to the AI tax assistant."""
    chat_repo = ChatMessageRepository(db)

    # Load recent history for context (last 20 messages)
    recent_messages = await chat_repo.find_by_tenant(user.tenant_id, limit=20)
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in recent_messages
        if msg.role in ("user", "assistant")
    ]

    # Persist user message
    await chat_repo.create_message(
        tenant_id=user.tenant_id,
        user_id=user.id,
        role="user",
        content=data.content,
    )

    tenant_context = {
        "tenant_id": str(user.tenant_id),
        "user_name": user.full_name,
    }

    # Process through agent (with tool execution)
    result = await process_message(
        user_message=data.content,
        conversation_history=conversation_history,
        tenant_context=tenant_context,
        db=db,
    )

    # Persist assistant response
    await chat_repo.create_message(
        tenant_id=user.tenant_id,
        user_id=user.id,
        role="assistant",
        content=result["response"],
        tool_calls=result.get("tool_calls") or None,
    )

    return ok({
        "role": "assistant",
        "content": result["response"],
        "tool_calls": result.get("tool_calls", []),
    })


@router.post("/stream")
async def stream_message(
    data: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Stream a response from the AI tax assistant via SSE."""
    chat_repo = ChatMessageRepository(db)

    # Load recent history
    recent_messages = await chat_repo.find_by_tenant(user.tenant_id, limit=20)
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in recent_messages
        if msg.role in ("user", "assistant")
    ]

    # Persist user message
    await chat_repo.create_message(
        tenant_id=user.tenant_id,
        user_id=user.id,
        role="user",
        content=data.content,
    )

    tenant_context = {
        "tenant_id": str(user.tenant_id),
        "user_name": user.full_name,
    }

    async def event_generator():
        full_response = ""
        try:
            async for token in process_message_stream(
                user_message=data.content,
                conversation_history=conversation_history,
                tenant_context=tenant_context,
                db=db,
            ):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Persist assistant response after streaming completes
            await chat_repo.create_message(
                tenant_id=user.tenant_id,
                user_id=user.id,
                role="assistant",
                content=full_response,
            )

            yield f"data: {json.dumps({'done': True, 'content': full_response})}\n\n"
        except Exception as e:
            error_msg = f"Sorry, an error occurred: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def get_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get chat history from database."""
    chat_repo = ChatMessageRepository(db)
    offset = (page - 1) * limit
    messages = await chat_repo.find_by_tenant(user.tenant_id, limit=limit, offset=offset)
    total = await chat_repo.count(tenant_id=user.tenant_id)

    return ok(
        [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ],
        meta={"total": total, "page": page, "limit": limit},
    )
