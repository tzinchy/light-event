import secrets
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import DomainError
from app.core.security import create_access_token
from app.core.sms import SmsProvider
from app.user.models import User
from app.user.repo import UserRepo


def _otp_code_key(phone: str) -> str:
    return f"otp:code:{phone}"


def _otp_attempts_key(phone: str) -> str:
    return f"otp:attempts:{phone}"


def _otp_req_key(phone: str) -> str:
    return f"otp:req:{phone}"


def _refresh_key(token: str) -> str:
    return f"auth:refresh:{token}"


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis, sms: SmsProvider, settings: Settings):
        self.session = session
        self.redis = redis
        self.sms = sms
        self.settings = settings
        self.users = UserRepo(session)

    async def request_otp(self, phone: str) -> None:
        req_key = _otp_req_key(phone)
        requests_made = await self.redis.incr(req_key)
        if requests_made == 1:
            await self.redis.expire(req_key, self.settings.otp_request_window_sec)
        if requests_made > self.settings.otp_request_limit:
            raise DomainError(429, "Слишком много запросов кода — попробуйте позже")

        code = f"{secrets.randbelow(10**6):06d}"
        await self.redis.set(_otp_code_key(phone), code, ex=self.settings.otp_ttl_sec)
        await self.redis.delete(_otp_attempts_key(phone))
        await self.sms.send_otp(phone, code)

    async def verify_otp(self, phone: str, code: str) -> tuple[dict, User]:
        stored = await self.redis.get(_otp_code_key(phone))
        if stored is None:
            raise DomainError(401, "Код не запрошен или истёк")

        attempts_key = _otp_attempts_key(phone)
        attempts = await self.redis.incr(attempts_key)
        if attempts == 1:
            await self.redis.expire(attempts_key, self.settings.otp_ttl_sec)
        if attempts > self.settings.otp_verify_max_attempts:
            await self.redis.delete(_otp_code_key(phone))
            raise DomainError(429, "Превышено число попыток — запросите новый код")

        if not secrets.compare_digest(stored, code):
            raise DomainError(401, "Неверный код")

        await self.redis.delete(_otp_code_key(phone), attempts_key)

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
