from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class RecommendationResponse(BaseModel):
    id: UUID
    business_id: UUID
    title: str
    description: Optional[str] = None
    priority: str
    category: Optional[str] = None
    status: str
    estimated_impact: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationsListResponse(BaseModel):
    recommendations: list[RecommendationResponse]


class RecommendationStatusUpdate(BaseModel):
    status: str
