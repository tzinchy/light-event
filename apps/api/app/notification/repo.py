from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.notification.models import Notification


class NotificationRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, notification: Notification) -> None:
        self.session.add(notification)

    async def list_for_user(self, user_uuid: UUID, limit: int = 50) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_uuid == user_uuid)
            .order_by(Notification.notification_uuid.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def unread_count(self, user_uuid: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_uuid == user_uuid, Notification.read_at.is_(None))
        )
        return result.scalar_one()

    async def mark_all_read(self, user_uuid: UUID) -> None:
        await self.session.execute(
            update(Notification)
            .where(Notification.user_uuid == user_uuid, Notification.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        )
