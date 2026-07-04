from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.models import User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_uuid: UUID) -> User | None:
        return await self.session.get(User, user_uuid)

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_with_email(self, email: str) -> User:
        """Регистрация по e-mail-OTP: почта сразу подтверждена самим фактом входа."""
        user = User(email=email, email_verified_at=datetime.now(timezone.utc))
        self.session.add(user)
        await self.session.flush()
        return user

    async def set_pd_consent(self, user: User) -> User:
        user.pd_consent_at = datetime.now(timezone.utc)
        await self.session.flush()
        return user
