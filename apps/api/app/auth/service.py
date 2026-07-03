import secrets
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import DomainError
from app.core.otp import OtpStore
from app.core.security import create_access_token
from app.core.sms import SmsProvider
from app.user.models import User
from app.user.repo import UserRepo


def _refresh_key(token: str) -> str:
    return f"auth:refresh:{token}"


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis, sms: SmsProvider, settings: Settings):
        self.session = session
        self.redis = redis
        self.sms = sms
        self.settings = settings
        self.users = UserRepo(session)
        self.otp = OtpStore(redis, settings)

    async def request_otp(self, phone: str) -> None:
        code = await self.otp.issue("sms", phone)
        await self.sms.send_otp(phone, code)

    async def verify_otp(self, phone: str, code: str) -> tuple[dict, User]:
        await self.otp.verify("sms", phone, code)

        user = await self.users.get_by_phone(phone)
        is_new = user is None
        if user is None:
            user = await self.users.create(phone)
        tokens = await self._issue_tokens(user.user_uuid)
        return {**tokens, "is_new_user": is_new}, user

    async def refresh(self, refresh_token: str) -> dict:
        user_uuid = await self.redis.getdel(_refresh_key(refresh_token))
        if user_uuid is None:
            raise DomainError(401, "Недействительный refresh-токен")
        user = await self.users.get(UUID(user_uuid))
        if user is None or not user.is_active:
            raise DomainError(401, "Пользователь не найден или заблокирован")
        return await self._issue_tokens(user.user_uuid)

    async def logout(self, refresh_token: str) -> None:
        await self.redis.delete(_refresh_key(refresh_token))

    async def set_pd_consent(self, user: User) -> User:
        return await self.users.set_pd_consent(user)

    async def _issue_tokens(self, user_uuid: UUID) -> dict:
        access = create_access_token(user_uuid, self.settings.app_secret_key, self.settings.access_token_ttl_sec)
        refresh = secrets.token_urlsafe(32)
        await self.redis.set(_refresh_key(refresh), str(user_uuid), ex=self.settings.refresh_token_ttl_sec)
        return {"access_token": access, "refresh_token": refresh}
