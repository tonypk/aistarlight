from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    content: str
    context: dict | None = None  # optional context like current report_type


class ChatMessageResponse(BaseModel):
    role: str
    content: str
    metadata: dict | None = None


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    total: int
