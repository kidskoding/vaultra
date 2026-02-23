from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class BusinessInfo(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithBusinessesResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    businesses: list[BusinessInfo] = []

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    user: UserWithBusinessesResponse
    token: str
