from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class BusinessMembership(BaseModel):
    id: UUID
    name: str
    role: str

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: UUID
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    businesses: list[BusinessMembership] = []

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class BusinessCreate(BaseModel):
    name: str
    legal_entity: Optional[str] = None
    industry: Optional[str] = None
    revenue_estimate: Optional[Decimal] = None
    founded_at: Optional[date] = None


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    legal_entity: Optional[str] = None
    industry: Optional[str] = None
    revenue_estimate: Optional[Decimal] = None
    founded_at: Optional[date] = None


class BusinessResponse(BaseModel):
    id: UUID
    name: str
    legal_entity: Optional[str] = None
    industry: Optional[str] = None
    revenue_estimate: Optional[Decimal] = None
    founded_at: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True
