from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class MetricsResponse(BaseModel):
    business_id: UUID
    period_start: date
    period_end: date
    revenue_total: Optional[Decimal] = None
    revenue_volatility: Optional[Decimal] = None
    chargeback_count: int = 0
    chargeback_ratio: Optional[Decimal] = None
    refund_count: int = 0
    refund_ratio: Optional[Decimal] = None
    payout_reliability: Optional[Decimal] = None
    transaction_count: int = 0
    average_transaction_size: Optional[Decimal] = None
    mrr: Optional[Decimal] = None

    class Config:
        from_attributes = True


class MetricsHistoryResponse(BaseModel):
    metrics: list[MetricsResponse]


class ReadinessResponse(BaseModel):
    business_id: UUID
    score: int
    tier: str
    components: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReadinessHistoryResponse(BaseModel):
    scores: list[ReadinessResponse]
