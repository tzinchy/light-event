from sqlalchemy.ext.asyncio import AsyncSession

from app.favorite.repo import FavoriteRepo
from app.notification.models import Notification
from app.notification.repo import NotificationRepo
from app.notification.schemas import NotificationListOut, NotificationOut
from app.user.models import User
from app.vacancy.models import Vacancy


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NotificationRepo(session)
        self.favorites = FavoriteRepo(session)

    async def notify_new_vacancy(self, vacancy: Vacancy) -> None:
        """Уведомить подписчиков компании о новой опубликованной смене (PLAN §11.8)."""
        for user_uuid in await self.favorites.follower_uuids(vacancy.company_uuid):
            self.repo.add(
                Notification(
                    user_uuid=user_uuid,
                    kind="new_vacancy",
                    title=f"Новая смена: {vacancy.event_title}",
                    company_uuid=vacancy.company_uuid,
                    vacancy_uuid=vacancy.vacancy_uuid,
                )
            )
        await self.session.flush()

    async def list(self, actor: User) -> NotificationListOut:
        items = await self.repo.list_for_user(actor.user_uuid)
        return NotificationListOut(
            unread=await self.repo.unread_count(actor.user_uuid),
            items=[NotificationOut.model_validate(n) for n in items],
        )

    async def mark_read(self, actor: User) -> None:
        await self.repo.mark_all_read(actor.user_uuid)
        await self.session.flush()
