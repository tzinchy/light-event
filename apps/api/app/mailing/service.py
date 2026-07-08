from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.email import EmailProvider, otp_email
from app.core.errors import DomainError
from app.mailing.models import EmailKind, EmailMessageLog, EmailStatus
from app.mailing.repo import MailingRepo


class MailingService:
    """Отправка писем с журналом: запись в email_message при любом исходе.

    Журнал пишется в отдельной транзакции, чтобы запись о неудаче переживала
    откат основной (ошибка отправки → DomainError 502 → rollback запроса).
    """

    def __init__(self, session_factory: async_sessionmaker, provider: EmailProvider):
        self.session_factory = session_factory
        self.provider = provider

    async def send_otp(self, to_email: str, code: str) -> None:
        subject, body = otp_email(code)
        error: str | None = None
        try:
            await self.provider.send_otp(to_email, code)
        except Exception as exc:  # noqa: BLE001 — журнал фиксирует любую ошибку отправки
            error = str(exc) or type(exc).__name__
        await self._log(to_email=to_email, subject=subject, body=body, kind=EmailKind.otp, error=error)
        if error is not None:
            raise DomainError(502, "Не удалось отправить письмо")

    async def send_custom(self, *, to_email: str, subject: str, body: str, created_by: UUID) -> EmailMessageLog:
        error: str | None = None
        try:
            await self.provider.send(to_email, subject, body)
        except Exception as exc:  # noqa: BLE001
            error = str(exc) or type(exc).__name__
        message = await self._log(
            to_email=to_email, subject=subject, body=body, kind=EmailKind.admin, error=error, created_by=created_by
        )
        if error is not None:
            raise DomainError(502, "Не удалось отправить письмо")
        return message

    async def _log(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
        kind: EmailKind,
        error: str | None,
        created_by: UUID | None = None,
    ) -> EmailMessageLog:
        async with self.session_factory() as session:
            async with session.begin():
                message = EmailMessageLog(
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    kind=kind.value,
                    status=(EmailStatus.failed if error else EmailStatus.sent).value,
                    error=error,
                    created_by=created_by,
                )
                MailingRepo(session).add(message)
                await session.flush()
                await session.refresh(message)
        return message
