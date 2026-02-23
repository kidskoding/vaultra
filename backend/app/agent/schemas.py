from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ChatRequest(BaseModel):
    business_id: UUID
    message: str
    conversation_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    response: str
    tool_calls: list = []


class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    business_id: UUID
    messages: list[MessageResponse]

    class Config:
        from_attributes = True
