from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, email: str, name: str, password: str) -> User:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-Mail bereits registriert.",
            )

        user = User(
            email=email,
            name=name,
            password_hash=hash_password(password),
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> tuple[User, str]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-Mail oder Passwort falsch.",
            )

        token = create_access_token({"sub": str(user.id)})
        return user, token
