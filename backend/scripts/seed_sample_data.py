import asyncio
import os
import sys
from datetime import date, timedelta
from uuid import UUID

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.config import settings  # type: ignore  # noqa: E402
from app.shared.database import AsyncSessionLocal  # type: ignore  # noqa: E402
from app.shared.models import Business, FinancialMetricSnapshot, ReadinessScore  # type: ignore  # noqa: E402


async def seed_for_business(business_id: UUID) -> None:
    async with AsyncSessionLocal() as session:
        # Ensure business exists
        business = await session.get(Business, business_id)
        if not business:
            business = Business(
                id=business_id,
                name="Demo Business",
                industry="saas",
            )
            session.add(business)

        # Simple metrics history: 6 monthly snapshots ending today
        today = date.today()
        first_day_this_month = today.replace(day=1)
        periods: list[tuple[date, date]] = []
        current_end = first_day_this_month - timedelta(days=1)
        for _ in range(6):
            start = current_end.replace(day=1)
            periods.append((start, current_end))
            current_end = start - timedelta(days=1)

        # Newest first
        periods = list(reversed(periods))

        base_revenue = 220_000
        base_mrr = 18_000

        for i, (start, end) in enumerate(periods):
            # Small upward trend with slight noise
            revenue_total = base_revenue + i * 5_000
            mrr = base_mrr + i * 1_000
            revenue_volatility = 0.16 - i * 0.006  # drifts down slightly
            chargeback_ratio = 0.004 - i * 0.0001
            payout_reliability = 0.94 + i * 0.008

            snapshot = FinancialMetricSnapshot(
                business_id=business_id,
                period_start=start,
                period_end=end,
                revenue_total=revenue_total,
                revenue_volatility=max(revenue_volatility, 0.05),
                chargeback_count=2 + i,
                chargeback_ratio=max(chargeback_ratio, 0.0015),
                refund_count=5 + i,
                refund_ratio=0.012,
                payout_reliability=min(payout_reliability, 0.995),
                transaction_count=1400 + i * 100,
                average_transaction_size=140,
                mrr=mrr,
                metrics_json={},
            )
            session.add(snapshot)

        # Simple readiness scores over same periods (trend up slightly)
        for i, (_, end) in enumerate(periods):
            score_value = 70 + i * 3
            tier = "improving"
            if score_value >= 71:
                tier = "funding_ready"
            if score_value >= 86:
                tier = "highly_attractive"

            score = ReadinessScore(
                business_id=business_id,
                score=min(score_value, 95),
                tier=tier,
                components={
                    "revenue_stability": 0.7 + i * 0.04,
                    "risk_signals": 0.65 + i * 0.03,
                    "growth": 0.7 + i * 0.02,
                    "as_of": str(end),
                },
            )
            session.add(score)

        await session.commit()


async def main() -> None:
    bid_str = settings.VAULTRA_SEED_BUSINESS_ID
    if not bid_str:
        print("Set VAULTRA_SEED_BUSINESS_ID in backend/.env to the business_id you want to seed.")
        sys.exit(1)

    try:
        business_id = UUID(bid_str)
    except ValueError:
        print("VAULTRA_SEED_BUSINESS_ID must be a valid UUID.")
        sys.exit(1)

    await seed_for_business(business_id)
    print(f"Seeded sample metrics and readiness score for business {business_id}")


if __name__ == "__main__":
    asyncio.run(main())

