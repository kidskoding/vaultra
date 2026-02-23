from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.deps import get_current_user
from app.shared.models import User
from app.recommendations.schemas import RecommendationsListResponse, RecommendationResponse, RecommendationStatusUpdate
from app.recommendations.service import RecommendationsService
from app.users.service import UsersService

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations", response_model=RecommendationsListResponse)
async def get_recommendations(
    business_id: UUID,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await UsersService(db).assert_business_member(business_id, current_user.id)
    recs = await RecommendationsService(db).get_recommendations(business_id, status, priority)
    return {"recommendations": recs}


@router.patch("/recommendations/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: UUID,
    data: RecommendationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationsService(db).update_recommendation_status(recommendation_id, current_user.id, data.status)
