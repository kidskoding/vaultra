from arq import cron
from app.shared.database import AsyncSessionLocal


async def quickbooks_sync(ctx):
    async with AsyncSessionLocal() as db:
        from app.shared.models import IntegrationAccount
        from sqlalchemy import select
        result = await db.execute(select(IntegrationAccount).where(IntegrationAccount.provider == "quickbooks", IntegrationAccount.status == "active"))
        accounts = result.scalars().all()
        for account in accounts:
            from app.quickbooks.service import QuickBooksService
            try:
                await QuickBooksService(db).sync_financial_data(account.business_id)
            except Exception:
                pass


async def compute_metrics(ctx):
    async with AsyncSessionLocal() as db:
        from app.shared.models import IntegrationAccount
        from sqlalchemy import select
        from datetime import date, timedelta
        result = await db.execute(select(IntegrationAccount).where(IntegrationAccount.provider == "quickbooks", IntegrationAccount.status == "active"))
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
        result = await db.execute(select(IntegrationAccount).where(IntegrationAccount.provider == "quickbooks", IntegrationAccount.status == "active"))
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
        result = await db.execute(select(IntegrationAccount).where(IntegrationAccount.provider == "quickbooks", IntegrationAccount.status == "active"))
        accounts = result.scalars().all()
        for account in accounts:
            from app.recommendations.service import RecommendationsService
            await RecommendationsService(db).generate_recommendations(account.business_id)


class WorkerSettings:
    functions = [quickbooks_sync, compute_metrics, compute_readiness, generate_recommendations]
    cron_jobs = [
        cron(quickbooks_sync, minute={0, 15, 30, 45}),
        cron(compute_metrics, minute=0),
        cron(compute_readiness, minute=5),
        cron(generate_recommendations, hour=2, minute=0),
    ]
    redis_settings = None
