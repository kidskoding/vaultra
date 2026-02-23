from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.deps import get_current_user
from app.shared.models import User
from app.users.schemas import UserUpdate, BusinessCreate, BusinessUpdate, BusinessResponse
from app.users.service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await UsersService(db).get_user_profile(current_user.id)


@router.patch("/me")
async def update_me(data: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await UsersService(db).update_user_profile(current_user.id, data.model_dump(exclude_none=True))


@router.post("/businesses", response_model=BusinessResponse, status_code=201)
async def create_business(data: BusinessCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await UsersService(db).create_business(current_user.id, data)


@router.patch("/businesses/{business_id}", response_model=BusinessResponse)
async def update_business(business_id: UUID, data: BusinessUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await UsersService(db).update_business(business_id, current_user.id, data.model_dump(exclude_none=True))
