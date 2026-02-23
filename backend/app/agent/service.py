from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.shared.models import AgentConversation, AgentMessage
from app.config import settings


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def chat(self, business_id: UUID, user_id: UUID, message: str, conversation_id: UUID | None = None) -> dict:
        if conversation_id:
            result = await self.db.execute(
                select(AgentConversation).where(AgentConversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Conversation not found"}})
        else:
            conversation = AgentConversation(business_id=business_id, user_id=user_id)
            self.db.add(conversation)
            await self.db.flush()

        tool_results = {}
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in ["readiness", "score", "ready", "funding"]):
            tool_results["readiness"] = await self.get_readiness_breakdown(business_id)
        if any(kw in msg_lower for kw in ["recommend", "improve", "fix", "action"]):
            tool_results["recommendations"] = await self.get_top_recommendations(business_id)
        if any(kw in msg_lower for kw in ["metric", "revenue", "chargeback", "payout"]):
            tool_results["metrics"] = await self.get_metric_summary(business_id)

        tool_results["business"] = await self.get_business_context(business_id)

        history_result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.conversation_id == conversation.id)
            .order_by(AgentMessage.created_at.asc())
        )
        history = history_result.scalars().all()

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Vaultra, a financial AI assistant that helps small businesses "
                    "improve their funding readiness. You have access to the business's financial "
                    "metrics, readiness score, and recommendations. Be concise, actionable, and data-driven.\n\n"
                    f"Business context: {tool_results}"
                ),
            }
        ]
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})

        llm_response = await self._call_llm(messages)

        user_msg = AgentMessage(conversation_id=conversation.id, role="user", content=message)
        assistant_msg = AgentMessage(conversation_id=conversation.id, role="assistant", content=llm_response)
        self.db.add(user_msg)
        self.db.add(assistant_msg)
        await self.db.commit()
        await self.db.refresh(assistant_msg)

        return {
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id,
            "response": llm_response,
            "tool_calls": list(tool_results.keys()),
        }

    async def get_conversation(self, conversation_id: UUID, user_id: UUID) -> dict:
        result = await self.db.execute(
            select(AgentConversation).where(AgentConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Conversation not found"}})
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Access denied"}})
        messages_result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.conversation_id == conversation_id)
            .order_by(AgentMessage.created_at.asc())
        )
        return {
            "id": conversation.id,
            "business_id": conversation.business_id,
            "messages": messages_result.scalars().all(),
        }

    async def get_readiness_breakdown(self, business_id: UUID) -> dict:
        from app.metrics.service import MetricsService
        try:
            score = await MetricsService(self.db).get_readiness_score(business_id)
            return {"score": score.score, "tier": score.tier, "components": score.components}
        except Exception:
            return {}

    async def get_top_recommendations(self, business_id: UUID, limit: int = 5) -> list:
        from app.recommendations.service import RecommendationsService
        recs = await RecommendationsService(self.db).get_recommendations(business_id, status="pending")
        return [{"title": r.title, "priority": r.priority, "estimated_impact": r.estimated_impact} for r in recs[:limit]]

    async def get_metric_summary(self, business_id: UUID) -> dict:
        from app.metrics.service import MetricsService
        try:
            snapshot = await MetricsService(self.db).get_latest_metrics(business_id)
            return {
                "revenue_total": float(snapshot.revenue_total) if snapshot.revenue_total else None,
                "revenue_volatility": float(snapshot.revenue_volatility) if snapshot.revenue_volatility else None,
                "chargeback_ratio": float(snapshot.chargeback_ratio) if snapshot.chargeback_ratio else None,
                "payout_reliability": float(snapshot.payout_reliability) if snapshot.payout_reliability else None,
            }
        except Exception:
            return {}

    async def get_business_context(self, business_id: UUID) -> dict:
        from app.shared.models import Business
        result = await self.db.execute(select(Business).where(Business.id == business_id))  # type: ignore
        # avoid circular import — Business is in shared models
        from app.shared.models import Business as B
        result = await self.db.execute(select(B).where(B.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            return {}
        return {"name": business.name, "industry": business.industry, "revenue_estimate": float(business.revenue_estimate) if business.revenue_estimate else None}

    async def search_knowledge(self, query: str, top_k: int = 5) -> list[dict]:
        return []

    async def _call_llm(self, messages: list[dict]) -> str:
        if settings.LLM_PROVIDER == "ollama":
            return await self._call_ollama(messages)
        return await self._call_openai(messages)

    async def _call_openai(self, messages: list[dict]) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I'm unable to respond at the moment. Please check your OpenAI configuration. ({e})"

    async def _call_ollama(self, messages: list[dict]) -> str:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={"model": settings.OLLAMA_MODEL, "messages": messages, "stream": False},
                    timeout=60,
                )
                return response.json()["message"]["content"]
        except Exception as e:
            return f"I'm unable to respond at the moment. Please check your Ollama configuration. ({e})"
