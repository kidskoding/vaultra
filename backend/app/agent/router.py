from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.deps import get_current_user
from app.shared.models import User
from app.agent.schemas import ChatRequest, ChatResponse, ConversationResponse
from app.agent.service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AgentService(db).chat(data.business_id, current_user.id, data.message, data.conversation_id)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AgentService(db).get_conversation(conversation_id, current_user.id)
