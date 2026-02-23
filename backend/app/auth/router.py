from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.deps import get_current_user
from app.shared.models import User
from app.auth.schemas import SignupRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    from app.auth.service import AuthService
    from app.users.service import UsersService
    service = AuthService(db)
    user, token = await service.signup(data.email, data.password, data.name)
    businesses = await UsersService(db).get_user_businesses(user.id)
    return {"user": {**user.__dict__, "businesses": businesses}, "token": token}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    from app.auth.service import AuthService
    from app.users.service import UsersService
    service = AuthService(db)
    user, token = await service.login(data.email, data.password)
    businesses = await UsersService(db).get_user_businesses(user.id)
    return {"user": {**user.__dict__, "businesses": businesses}, "token": token}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.users.service import UsersService
    return await UsersService(db).get_user_profile(current_user.id)
