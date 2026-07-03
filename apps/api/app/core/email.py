import logging
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailProvider(Protocol):
    """Отправка кодов подтверждения на почту."""

    async def send_otp(self, email: str, code: str) -> None: ...


class ConsoleEmailProvider:
    """Dev-реализация без SMTP-настроек: код уходит в лог."""

    async def send_otp(self, email: str, code: str) -> None:
        logger.info("Код подтверждения почты для %s: %s", email, code)


class SmtpEmailProvider:
    """Реальный SMTP (Brevo/Mailpit): хост и учётка из настроек."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_otp(self, email: str, code: str) -> None:
        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = email
        message["Subject"] = f"{code} — код подтверждения light-event"
        message.set_content(
            f"Ваш код подтверждения почты: {code}\n\n"
            "Код действует 5 минут. Если вы не запрашивали его — просто проигнорируйте письмо."
        )
        await aiosmtplib.send(
            message,
            hostname=self.settings.smtp_host,
            port=self.settings.smtp_port,
            username=self.settings.smtp_user or None,
            password=self.settings.smtp_password or None,
            use_tls=self.settings.smtp_use_tls,
        )


def build_email_provider(settings: Settings) -> EmailProvider:
    if settings.smtp_host:
        return SmtpEmailProvider(settings)
    return ConsoleEmailProvider()
