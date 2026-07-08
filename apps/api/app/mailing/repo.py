from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mailing.models import EmailMessageLog


class MailingRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, message: EmailMessageLog) -> None:
        self.session.add(message)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[EmailMessageLog]:
        result = await self.session.execute(
            select(EmailMessageLog)
            # UUIDv7 монотонен по времени — сортировка по PK даёт «новые сверху»
            .order_by(EmailMessageLog.email_message_uuid.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())
