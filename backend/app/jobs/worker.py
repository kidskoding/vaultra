from arq import cron
from app.shared.database import AsyncSessionLocal


async def stripe_sync(ctx):
    async with AsyncSessionLocal() as db:
        from app.shared.models import IntegrationAccount
        from sqlalchemy import select
        result = await db.execute(select(IntegrationAccount).where(IntegrationAccount.provider == "stripe", IntegrationAccount.status == "active"))
        accounts = result.scalars().all()
        for account in accounts:
            from app.stripe.service import StripeService
            await StripeService(db).sync_account_data(account.external_id, account.business_id)


async def compute_metrics(ctx):
    async with AsyncSessionLocal() as db:
        from app.shared.models import IntegrationAccount
        from sqlalchemy import select
        from datetime import date, timedelta
        result = await db.execute(select(IntegrationAccount).where(IntegrationAccount.provider == "stripe", IntegrationAccount.status == "active"))
        accounts = result.scalars().all()
        for account in accounts:
            from app.metrics.service import MetricsService
            end = date.today()
            start = end - timedelta(days=30)
            await MetricsService(db).compute_metrics(account.business_id, start, end)


async def compute_readiness(ctx):
    async with AsyncSessionLocal() as db:
        from app.shared.models import IntegrationAccount, FinancialMetricSnapshot
        from sqlalchemy import select
        result = await db.execute(select(IntegrationAccount).where(IntegrationAccount.provider == "stripe", IntegrationAccount.status == "active"))
        accounts = result.scalars().all()
        for account in accounts:
            from app.metrics.service import MetricsService
            svc = MetricsService(db)
            try:
                snapshot = await svc.get_latest_metrics(account.business_id)
                await svc.compute_readiness_score(account.business_id, snapshot)
            except Exception:
                pass


async def generate_recommendations(ctx):
    async with AsyncSessionLocal() as db:
        from app.shared.models import IntegrationAccount
        from sqlalchemy import select
        result = await db.execute(select(IntegrationAccount).where(IntegrationAccount.provider == "stripe", IntegrationAccount.status == "active"))
        accounts = result.scalars().all()
        for account in accounts:
            from app.recommendations.service import RecommendationsService
            await RecommendationsService(db).generate_recommendations(account.business_id)


class WorkerSettings:
    functions = [stripe_sync, compute_metrics, compute_readiness, generate_recommendations]
    cron_jobs = [
        cron(stripe_sync, minute={0, 15, 30, 45}),
        cron(compute_metrics, minute=0),
        cron(compute_readiness, minute=5),
        cron(generate_recommendations, hour=2, minute=0),
    ]
    redis_settings = None
