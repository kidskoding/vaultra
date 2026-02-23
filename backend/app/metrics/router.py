from uuid import UUID
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.deps import get_current_user
from app.shared.models import User
from app.metrics.schemas import MetricsResponse, MetricsHistoryResponse, ReadinessResponse, ReadinessHistoryResponse
from app.metrics.service import MetricsService
from app.users.service import UsersService

router = APIRouter(tags=["metrics"])


async def assert_member(business_id: UUID, current_user: User, db: AsyncSession):
    await UsersService(db).assert_business_member(business_id, current_user.id)


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await assert_member(business_id, current_user, db)
    return await MetricsService(db).get_latest_metrics(business_id)


@router.get("/metrics/history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    business_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await assert_member(business_id, current_user, db)
    metrics = await MetricsService(db).get_metric_history(business_id, start_date, end_date)
    return {"metrics": metrics}


@router.get("/readiness", response_model=ReadinessResponse)
async def get_readiness(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await assert_member(business_id, current_user, db)
    return await MetricsService(db).get_readiness_score(business_id)


@router.get("/readiness/history", response_model=ReadinessHistoryResponse)
async def get_readiness_history(
    business_id: UUID,
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await assert_member(business_id, current_user, db)
    scores = await MetricsService(db).get_readiness_history(business_id, limit)
    return {"scores": scores}
