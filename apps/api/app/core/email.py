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


def otp_email_html(code: str) -> str:
    """HTML-версия OTP-письма: тёмная шапка light-event, крупный код-моноширинный блок."""
    spaced = " ".join(code)  # читаемее при копировании глазами
    return f"""\
<!DOCTYPE html>
<html lang="ru">
<body style="margin:0;padding:0;background:#f4f4f5;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:440px;background:#ffffff;border-radius:16px;overflow:hidden;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
        <tr><td style="background:#18181b;padding:28px 32px;">
          <span style="color:#ffffff;font-size:18px;font-weight:700;letter-spacing:.3px;">light-event</span>
        </td></tr>
        <tr><td style="padding:36px 32px 12px;">
          <p style="margin:0 0 8px;color:#18181b;font-size:18px;font-weight:600;">Код подтверждения почты</p>
          <p style="margin:0;color:#71717a;font-size:14px;line-height:1.5;">Введите этот код, чтобы подтвердить адрес.</p>
        </td></tr>
        <tr><td style="padding:8px 32px 32px;">
          <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:20px;text-align:center;">
            <span style="color:#16a34a;font-size:34px;font-weight:700;letter-spacing:10px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;">{spaced}</span>
          </div>
          <p style="margin:20px 0 0;color:#a1a1aa;font-size:13px;line-height:1.5;text-align:center;">Код действует 5 минут. Если вы не запрашивали его — просто проигнорируйте письмо.</p>
        </td></tr>
      </table>
      <p style="margin:20px 0 0;color:#a1a1aa;font-size:12px;">© light-event</p>
    </td></tr>
  </table>
</body>
</html>"""


class EmailProvider(Protocol):
    """Отправка писем: OTP-коды и произвольные сообщения (журнал ведёт MailingService)."""

    async def send_otp(self, email: str, code: str) -> None: ...

    async def send(self, email: str, subject: str, body: str, html: str | None = None) -> None: ...


class ConsoleEmailProvider:
    """Dev-реализация без SMTP-настроек: письмо уходит в лог."""

    async def send_otp(self, email: str, code: str) -> None:
        logger.info("Код подтверждения почты для %s: %s", email, code)

    async def send(self, email: str, subject: str, body: str, html: str | None = None) -> None:
        logger.info("Письмо для %s: %s\n%s", email, subject, body)


class SmtpEmailProvider:
    """Реальный SMTP (Яндекс/Brevo/Mailpit): хост и учётка из настроек."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_otp(self, email: str, code: str) -> None:
        subject, body = otp_email(code)
        await self.send(email, subject, body, html=otp_email_html(code))

    async def send(self, email: str, subject: str, body: str, html: str | None = None) -> None:
        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)
        if html is not None:
            message.add_alternative(html, subtype="html")
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
