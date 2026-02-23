from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException
from app.shared.models import User
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, email: str, password: str, name: str) -> tuple[User, str]:
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail={"error": {"code": "CONFLICT", "message": "Email already registered"}})
        if len(password) < 8:
            raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Password must be at least 8 characters"}})
        user = User(email=email, hashed_password=pwd_context.hash(password), name=name)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user, self._create_token(user)

    async def login(self, email: str, password: str) -> tuple[User, str]:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not user.hashed_password or not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status_code=401, detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid credentials"}})
        return user, self._create_token(user)

    async def get_current_user(self, token: str) -> User:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
            user_id: str = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid token"}})
        except JWTError:
            raise HTTPException(status_code=401, detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid token"}})
        result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail={"error": {"code": "UNAUTHORIZED", "message": "User not found"}})
        return user

    def _create_token(self, user: User) -> str:
        expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
        return jwt.encode(
            {"user_id": str(user.id), "email": user.email, "exp": expire},
            settings.JWT_SECRET,
            algorithm=ALGORITHM,
        )
