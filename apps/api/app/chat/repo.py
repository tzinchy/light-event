from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.models import Application
from app.chat.models import ChatMessage, ChatMessageRevision, ChatThread
from app.company.models import Company
from app.team.models import TeamMember
from app.user.models import User
from app.vacancy.models import Vacancy


class ChatRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, obj) -> None:
        self.session.add(obj)

    async def get_thread(self, chat_thread_uuid: UUID) -> ChatThread | None:
        return await self.session.get(ChatThread, chat_thread_uuid)

    async def get_thread_by_application(self, application_uuid: UUID) -> ChatThread | None:
        result = await self.session.execute(
            select(ChatThread).where(ChatThread.application_uuid == application_uuid)
        )
        return result.scalar_one_or_none()

    async def list_threads_for_user(self, user_uuid: UUID) -> list[tuple]:
        """Треды пользователя: его заявки + заявки на смены компаний, где он в команде."""
        my_companies = select(TeamMember.company_uuid).where(TeamMember.user_uuid == user_uuid)
        result = await self.session.execute(
            select(ChatThread, Application, Vacancy, Company.name, User.name)
            .join(Application, Application.application_uuid == ChatThread.application_uuid)
            .join(Vacancy, Vacancy.vacancy_uuid == Application.vacancy_uuid)
            .join(Company, Company.company_uuid == Vacancy.company_uuid)
            .join(User, User.user_uuid == Application.user_uuid)
            .where(
                (Application.user_uuid == user_uuid) | Vacancy.company_uuid.in_(my_companies)
            )
            .order_by(ChatThread.chat_thread_uuid.desc())
        )
        return [tuple(row) for row in result.all()]

    async def last_message(self, chat_thread_uuid: UUID) -> ChatMessage | None:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_thread_uuid == chat_thread_uuid)
            .order_by(ChatMessage.chat_message_uuid.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def unread_count(self, chat_thread_uuid: UUID, reader_uuid: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ChatMessage)
            .where(
                ChatMessage.chat_thread_uuid == chat_thread_uuid,
                ChatMessage.sender_uuid != reader_uuid,
                ChatMessage.read_at.is_(None),
            )
        )
        return result.scalar_one()

    async def list_messages(self, chat_thread_uuid: UUID) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_thread_uuid == chat_thread_uuid)
            .order_by(ChatMessage.chat_message_uuid)
        )
        return list(result.scalars())

    async def thread_participant_uuids(self, chat_thread_uuid: UUID) -> set[UUID]:
        """Участники треда: соискатель заявки + вся команда компании смены."""
        row = (
            await self.session.execute(
                select(Application.user_uuid, Vacancy.company_uuid)
                .select_from(ChatThread)
                .join(Application, Application.application_uuid == ChatThread.application_uuid)
                .join(Vacancy, Vacancy.vacancy_uuid == Application.vacancy_uuid)
                .where(ChatThread.chat_thread_uuid == chat_thread_uuid)
            )
        ).first()
        if row is None:
            return set()
        applicant_uuid, company_uuid = row
        members = (
            await self.session.execute(
                select(TeamMember.user_uuid).where(TeamMember.company_uuid == company_uuid)
            )
        ).scalars()
        return {applicant_uuid, *members}

    async def counterpart_uuids(self, user_uuid: UUID) -> set[UUID]:
        """Собеседники по всем тредам пользователя — для рассылки онлайн-статуса."""
        result: set[UUID] = set()
        for thread, *_ in await self.list_threads_for_user(user_uuid):
            result |= await self.thread_participant_uuids(thread.chat_thread_uuid)
        result.discard(user_uuid)
        return result

    async def get_message(self, chat_message_uuid: UUID) -> ChatMessage | None:
        return await self.session.get(ChatMessage, chat_message_uuid)

    async def revisions(self, chat_message_uuid: UUID) -> list[ChatMessageRevision]:
        result = await self.session.execute(
            select(ChatMessageRevision)
            .where(ChatMessageRevision.chat_message_uuid == chat_message_uuid)
            .order_by(ChatMessageRevision.chat_message_revision_uuid)
        )
        return list(result.scalars())

    async def moderated_messages(self, limit: int = 100) -> list[tuple[ChatMessage, str]]:
        """Для админа: отредактированные/удалённые сообщения с названием события (§11.11)."""
        result = await self.session.execute(
            select(ChatMessage, Vacancy.event_title)
            .join(ChatThread, ChatThread.chat_thread_uuid == ChatMessage.chat_thread_uuid)
            .join(Application, Application.application_uuid == ChatThread.application_uuid)
            .join(Vacancy, Vacancy.vacancy_uuid == Application.vacancy_uuid)
            .where((ChatMessage.edited_at.isnot(None)) | (ChatMessage.deleted_at.isnot(None)))
            .order_by(ChatMessage.chat_message_uuid.desc())
            .limit(limit)
        )
        return [(m, title) for m, title in result.all()]

    async def mark_read(self, chat_thread_uuid: UUID, reader_uuid: UUID) -> None:
        await self.session.execute(
            update(ChatMessage)
            .where(
                ChatMessage.chat_thread_uuid == chat_thread_uuid,
                ChatMessage.sender_uuid != reader_uuid,
                ChatMessage.read_at.is_(None),
            )
            .values(read_at=datetime.now(UTC))
        )
