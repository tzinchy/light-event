import logging
from typing import Protocol

import httpx

from app.core.config import Settings
from app.core.errors import DomainError

logger = logging.getLogger(__name__)


class SmsProvider(Protocol):
    """Отправка OTP-кодов. Реальный SMS-шлюз подключается реализацией этого интерфейса."""

    async def send_otp(self, phone: str, code: str) -> None: ...


class ConsoleSmsProvider:
    """Dev-реализация: код уходит в лог, никаких внешних вызовов."""

    async def send_otp(self, phone: str, code: str) -> None:
        logger.info("OTP для %s: %s", phone, code)


class SmsRuProvider:
    """SMS.ru: ~4–6 ₽/SMS в проде; на собственный подтверждённый номер — бесплатно.

    Ключ: https://sms.ru → регистрация → API-ключ → SMS_RU_API_KEY в .env.
    """

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None):
        self.api_key = api_key
        self.client = client or httpx.AsyncClient(timeout=10)

    async def send_otp(self, phone: str, code: str) -> None:
        to = phone.lstrip("+")
        try:
            resp = await self.client.get(
                "https://sms.ru/sms/send",
                params={
                    "api_id": self.api_key,
                    "to": to,
                    "msg": f"{code} — код входа light-event",
                    "json": 1,
                },
            )
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.error("SMS.ru недоступен: %s", exc)
            raise DomainError(502, "Не удалось отправить SMS — попробуйте позже")

        sms_status = data.get("sms", {}).get(to, {})
        if data.get("status") != "OK" or sms_status.get("status") != "OK":
            logger.error("SMS.ru отклонил отправку на %s: %s", phone, sms_status or data)
            raise DomainError(502, "Не удалось отправить SMS — попробуйте позже")


def build_sms_provider(settings: Settings) -> SmsProvider:
    if settings.sms_ru_api_key:
        return SmsRuProvider(settings.sms_ru_api_key)
    return ConsoleSmsProvider()
