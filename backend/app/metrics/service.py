from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.shared.models import FinancialMetricSnapshot, ReadinessScore


TIER_THRESHOLDS = [
    (86, "highly_attractive"),
    (71, "funding_ready"),
    (41, "improving"),
    (0, "not_ready"),
]


class MetricsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_metrics(self, business_id: UUID) -> FinancialMetricSnapshot:
        result = await self.db.execute(
            select(FinancialMetricSnapshot)
            .where(FinancialMetricSnapshot.business_id == business_id)
            .order_by(FinancialMetricSnapshot.period_end.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "No metrics found"}})
        return snapshot

    async def get_metric_history(self, business_id: UUID, start_date: date | None, end_date: date | None) -> list[FinancialMetricSnapshot]:
        query = select(FinancialMetricSnapshot).where(FinancialMetricSnapshot.business_id == business_id)
        if start_date:
            query = query.where(FinancialMetricSnapshot.period_end >= start_date)
        if end_date:
            query = query.where(FinancialMetricSnapshot.period_end <= end_date)
        result = await self.db.execute(query.order_by(FinancialMetricSnapshot.period_end.desc()))
        return result.scalars().all()

    async def get_readiness_score(self, business_id: UUID) -> ReadinessScore:
        result = await self.db.execute(
            select(ReadinessScore)
            .where(ReadinessScore.business_id == business_id)
            .order_by(ReadinessScore.created_at.desc())
            .limit(1)
        )
        score = result.scalar_one_or_none()
        if not score:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "No readiness score found"}})
        return score

    async def get_readiness_history(self, business_id: UUID, limit: int = 30) -> list[ReadinessScore]:
        result = await self.db.execute(
            select(ReadinessScore)
            .where(ReadinessScore.business_id == business_id)
            .order_by(ReadinessScore.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def compute_readiness_score(self, business_id: UUID, snapshot: FinancialMetricSnapshot) -> ReadinessScore:
        score = 50
        components = {}

        if snapshot.revenue_volatility is not None:
            vol = float(snapshot.revenue_volatility)
            if vol > 0.5:
                score -= 10
            elif vol < 0.2:
                score += 5
            components["revenue_stability"] = max(0.0, 1.0 - vol)

        if snapshot.chargeback_ratio is not None:
            cb = float(snapshot.chargeback_ratio)
            if cb > 0.02:
                score -= 15
            elif cb < 0.005:
                score += 5
            components["risk_signals"] = max(0.0, 1.0 - cb * 10)

        if snapshot.payout_reliability is not None:
            pr = float(snapshot.payout_reliability)
            if pr > 0.95:
                score += 10
            elif pr < 0.80:
                score -= 10
            components["payout_reliability"] = pr

        score = max(0, min(100, score))
        tier = "not_ready"
        for threshold, tier_name in TIER_THRESHOLDS:
            if score >= threshold:
                tier = tier_name
                break

        readiness = ReadinessScore(
            business_id=business_id,
            score=score,
            tier=tier,
            components=components,
        )
        self.db.add(readiness)
        await self.db.commit()
        await self.db.refresh(readiness)
        return readiness

    async def compute_metrics(self, business_id: UUID, start_date: date, end_date: date) -> FinancialMetricSnapshot:
        pass
