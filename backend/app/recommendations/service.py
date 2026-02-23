from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.shared.models import Recommendation, FinancialMetricSnapshot, ReadinessScore


class RecommendationsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommendations(
        self, business_id: UUID, status: str | None = None, priority: str | None = None
    ) -> list[Recommendation]:
        query = select(Recommendation).where(Recommendation.business_id == business_id)
        if status:
            query = query.where(Recommendation.status == status)
        if priority:
            query = query.where(Recommendation.priority == priority)
        query = query.order_by(
            Recommendation.priority.desc(),
            Recommendation.created_at.desc(),
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_recommendation_status(self, recommendation_id: UUID, user_id: UUID, status: str) -> Recommendation:
        if status not in ("accepted", "dismissed"):
            raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Status must be accepted or dismissed"}})
        result = await self.db.execute(select(Recommendation).where(Recommendation.id == recommendation_id))
        rec = result.scalar_one_or_none()
        if not rec:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Recommendation not found"}})
        rec.status = status
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

    async def generate_recommendations(self, business_id: UUID) -> list[Recommendation]:
        result = await self.db.execute(
            select(FinancialMetricSnapshot)
            .where(FinancialMetricSnapshot.business_id == business_id)
            .order_by(FinancialMetricSnapshot.period_end.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()

        score_result = await self.db.execute(
            select(ReadinessScore)
            .where(ReadinessScore.business_id == business_id)
            .order_by(ReadinessScore.created_at.desc())
            .limit(1)
        )
        score = score_result.scalar_one_or_none()

        new_recs = []

        if snapshot:
            if snapshot.chargeback_ratio and float(snapshot.chargeback_ratio) > 0.02:
                new_recs.append(Recommendation(
                    business_id=business_id,
                    title="Reduce chargebacks",
                    description="Your chargeback ratio is above 2%. Consider improving dispute descriptors and customer communication.",
                    priority="high",
                    category="risk",
                    estimated_impact="+10-15 points",
                    metric_refs={"chargeback_ratio": float(snapshot.chargeback_ratio)},
                ))
            if snapshot.revenue_volatility and float(snapshot.revenue_volatility) > 0.5:
                new_recs.append(Recommendation(
                    business_id=business_id,
                    title="Stabilize revenue streams",
                    description="High revenue volatility detected. Diversifying revenue sources can improve your score.",
                    priority="medium",
                    category="cash_flow",
                    estimated_impact="+5-10 points",
                    metric_refs={"revenue_volatility": float(snapshot.revenue_volatility)},
                ))
            if snapshot.payout_reliability and float(snapshot.payout_reliability) < 0.80:
                new_recs.append(Recommendation(
                    business_id=business_id,
                    title="Improve payout timing",
                    description="Less than 80% of payouts are completing on time. Review your Stripe payout settings.",
                    priority="high",
                    category="cash_flow",
                    estimated_impact="+10 points",
                    metric_refs={"payout_reliability": float(snapshot.payout_reliability)},
                ))

        if score and score.score < 50:
            new_recs.append(Recommendation(
                business_id=business_id,
                title="Focus on core metrics",
                description="Your readiness score is below 50. Focus on reducing chargebacks and stabilizing revenue.",
                priority="medium",
                category="general",
                estimated_impact="Varies",
            ))

        for rec in new_recs:
            self.db.add(rec)
        await self.db.commit()
        return new_recs
