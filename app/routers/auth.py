from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await AuthService.register(db, data.email, data.name, data.password)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user, token = await AuthService.login(db, data.email, data.password)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user
