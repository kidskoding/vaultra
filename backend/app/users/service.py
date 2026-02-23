from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.shared.models import User, Business, UserBusinessMembership


class UsersService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_profile(self, user_id: UUID) -> dict:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "User not found"}})
        businesses = await self.get_user_businesses(user_id)
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "businesses": businesses,
        }

    async def update_user_profile(self, user_id: UUID, updates: dict) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "User not found"}})
        for key, value in updates.items():
            if value is not None:
                setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create_business(self, user_id: UUID, data) -> Business:
        business = Business(**{k: v for k, v in data.model_dump().items() if v is not None})
        self.db.add(business)
        await self.db.flush()
        membership = UserBusinessMembership(user_id=user_id, business_id=business.id, role="owner")
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(business)
        return business

    async def update_business(self, business_id: UUID, user_id: UUID, updates: dict) -> Business:
        result = await self.db.execute(
            select(UserBusinessMembership).where(
                UserBusinessMembership.business_id == business_id,
                UserBusinessMembership.user_id == user_id,
            )
        )
        membership = result.scalar_one_or_none()
        if not membership or membership.role not in ("owner", "admin"):
            raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Insufficient permissions"}})
        result = await self.db.execute(select(Business).where(Business.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Business not found"}})
        for key, value in updates.items():
            if value is not None:
                setattr(business, key, value)
        await self.db.commit()
        await self.db.refresh(business)
        return business

    async def get_user_businesses(self, user_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(Business, UserBusinessMembership.role)
            .join(UserBusinessMembership, Business.id == UserBusinessMembership.business_id)
            .where(UserBusinessMembership.user_id == user_id)
        )
        return [{"id": b.id, "name": b.name, "role": role} for b, role in result.all()]

    async def assert_business_member(self, business_id: UUID, user_id: UUID) -> None:
        result = await self.db.execute(
            select(UserBusinessMembership).where(
                UserBusinessMembership.business_id == business_id,
                UserBusinessMembership.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Access denied"}})
