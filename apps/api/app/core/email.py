import logging
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from app.core.config import Settings

logger = logging.getLogger(__name__)


def otp_email(code: str) -> tuple[str, str]:
    """Каноничный текст OTP-письма: (subject, body) — общий для провайдера и журнала."""
    return (
        f"{code} — код подтверждения light-event",
        f"Ваш код подтверждения почты: {code}\n\n"
        "Код действует 5 минут. Если вы не запрашивали его — просто проигнорируйте письмо.",
    )


class EmailProvider(Protocol):
    """Отправка писем: OTP-коды и произвольные сообщения (журнал ведёт MailingService)."""

    async def send_otp(self, email: str, code: str) -> None: ...

    async def send(self, email: str, subject: str, body: str) -> None: ...


class ConsoleEmailProvider:
    """Dev-реализация без SMTP-настроек: письмо уходит в лог."""

    async def send_otp(self, email: str, code: str) -> None:
        logger.info("Код подтверждения почты для %s: %s", email, code)

    async def send(self, email: str, subject: str, body: str) -> None:
        logger.info("Письмо для %s: %s\n%s", email, subject, body)


class SmtpEmailProvider:
    """Реальный SMTP (Яндекс/Brevo/Mailpit): хост и учётка из настроек."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_otp(self, email: str, code: str) -> None:
        subject, body = otp_email(code)
        await self.send(email, subject, body)

    async def send(self, email: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)
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
