"""Одноразовые коды в Redis: rate-limit запросов, TTL, лимит попыток.

Общая механика для всех каналов (sms, email) — вынесена из AuthService.
"""

import secrets

from redis.asyncio import Redis

from app.core.config import Settings
from app.core.errors import DomainError


class OtpStore:
    def __init__(self, redis: Redis, settings: Settings):
        self.redis = redis
        self.settings = settings

    def _key(self, kind: str, channel: str, destination: str) -> str:
        return f"otp:{channel}:{kind}:{destination}"

    async def issue(self, channel: str, destination: str) -> str:
        req_key = self._key("req", channel, destination)
        requests_made = await self.redis.incr(req_key)
        if requests_made == 1:
            await self.redis.expire(req_key, self.settings.otp_request_window_sec)
        if requests_made > self.settings.otp_request_limit:
            raise DomainError(429, "Слишком много запросов кода — попробуйте позже")

        code = f"{secrets.randbelow(10**6):06d}"
        await self.redis.set(self._key("code", channel, destination), code, ex=self.settings.otp_ttl_sec)
        await self.redis.delete(self._key("attempts", channel, destination))
        return code

    async def verify(self, channel: str, destination: str, code: str) -> None:
        code_key = self._key("code", channel, destination)
        stored = await self.redis.get(code_key)
        if stored is None:
            raise DomainError(401, "Код не запрошен или истёк")

        attempts_key = self._key("attempts", channel, destination)
        attempts = await self.redis.incr(attempts_key)
        if attempts == 1:
            await self.redis.expire(attempts_key, self.settings.otp_ttl_sec)
        if attempts > self.settings.otp_verify_max_attempts:
            await self.redis.delete(code_key)
            raise DomainError(429, "Превышено число попыток — запросите новый код")

        if not secrets.compare_digest(stored, code):
            raise DomainError(401, "Неверный код")

        await self.redis.delete(code_key, attempts_key)
