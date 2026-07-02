import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class SmsProvider(Protocol):
    """Отправка OTP-кодов. Реальный SMS-шлюз подключается реализацией этого интерфейса."""

    async def send_otp(self, phone: str, code: str) -> None: ...


class ConsoleSmsProvider:
    """Dev-реализация: код уходит в лог, никаких внешних вызовов."""

    async def send_otp(self, phone: str, code: str) -> None:
        logger.info("OTP для %s: %s", phone, code)
