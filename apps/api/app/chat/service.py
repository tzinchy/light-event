from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.repo import ApplicationRepo
from app.chat.models import ChatMessage, ChatMessageRevision, ChatThread
from app.chat.repo import ChatRepo
from app.chat.schemas import MessageOut, MessageSendIn, ThreadOut, message_out
from app.core.errors import DomainError
from app.core.permissions import ensure_membership
from app.user.models import User
from app.vacancy.repo import VacancyRepo


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ChatRepo(session)
        self.applications = ApplicationRepo(session)
        self.vacancies = VacancyRepo(session)

    async def _ensure_participant(self, actor: User, application) -> None:
        """Участники треда: соискатель заявки и команда компании смены."""
        if application.user_uuid == actor.user_uuid:
            return
        vacancy = await self.vacancies.get(application.vacancy_uuid)
        try:
            await ensure_membership(self.session, actor, vacancy.company_uuid)
        except DomainError:
            raise DomainError(403, "Нет доступа к этому чату") from None

    async def open_thread(self, actor: User, application_uuid: UUID) -> tuple[ChatThread, bool]:
        application = await self.applications.get(application_uuid)
        if application is None:
            raise DomainError(404, "Заявка не найдена")
        await self._ensure_participant(actor, application)
        thread = await self.repo.get_thread_by_application(application_uuid)
        if thread is not None:
            return thread, False
        thread = ChatThread(application_uuid=application_uuid)
        self.repo.add(thread)
        await self.session.flush()
        return thread, True

    async def _thread_with_access(self, actor: User, chat_thread_uuid: UUID) -> ChatThread:
        thread = await self.repo.get_thread(chat_thread_uuid)
        if thread is None:
            raise DomainError(404, "Чат не найден")
        application = await self.applications.get(thread.application_uuid)
        await self._ensure_participant(actor, application)
        return thread

    async def send(self, actor: User, chat_thread_uuid: UUID, data: MessageSendIn) -> ChatMessage:
        thread = await self._thread_with_access(actor, chat_thread_uuid)
        message = ChatMessage(
            chat_thread_uuid=thread.chat_thread_uuid, sender_uuid=actor.user_uuid, text=data.text
        )
        self.repo.add(message)
        await self.session.flush()
        return message

    async def list_messages(self, actor: User, chat_thread_uuid: UUID) -> list[ChatMessage]:
        thread = await self._thread_with_access(actor, chat_thread_uuid)
        return await self.repo.list_messages(thread.chat_thread_uuid)

    async def _own_message(self, actor: User, chat_message_uuid: UUID) -> ChatMessage:
        message = await self.repo.get_message(chat_message_uuid)
        if message is None:
            raise DomainError(404, "Сообщение не найдено")
        if message.sender_uuid != actor.user_uuid:
            raise DomainError(403, "Можно менять только свои сообщения")
        if message.deleted_at is not None:
            raise DomainError(409, "Сообщение удалено")
        return message

    async def edit(self, actor: User, chat_message_uuid: UUID, data: MessageSendIn) -> ChatMessage:
        """Правка своего сообщения: прежний текст уходит в ревизию (видна админу), ставится edited_at."""
        message = await self._own_message(actor, chat_message_uuid)
        self.repo.add(ChatMessageRevision(chat_message_uuid=message.chat_message_uuid, text=message.text))
        message.text = data.text
        message.edited_at = datetime.now(UTC)
        await self.session.flush()
        return message

    async def delete(self, actor: User, chat_message_uuid: UUID) -> ChatMessage:
        """Мягкое удаление: только флаг deleted_at, текст остаётся для админа (§11.11)."""
        message = await self._own_message(actor, chat_message_uuid)
        message.deleted_at = datetime.now(UTC)
        await self.session.flush()
        return message

    async def mark_read(self, actor: User, chat_thread_uuid: UUID) -> None:
        thread = await self._thread_with_access(actor, chat_thread_uuid)
        await self.repo.mark_read(thread.chat_thread_uuid, actor.user_uuid)
        await self.session.flush()

    async def list_threads(self, actor: User) -> list[ThreadOut]:
        rows = await self.repo.list_threads_for_user(actor.user_uuid)
        out: list[ThreadOut] = []
        for thread, application, vacancy, company_name, applicant_name in rows:
            last = await self.repo.last_message(thread.chat_thread_uuid)
            # для соискателя собеседник — организация, для команды — соискатель
            counterpart = company_name if application.user_uuid == actor.user_uuid else applicant_name
            out.append(
                ThreadOut(
                    chat_thread_uuid=thread.chat_thread_uuid,
                    application_uuid=application.application_uuid,
                    vacancy_uuid=vacancy.vacancy_uuid,
                    event_title=vacancy.event_title,
                    role_name=vacancy.role_name,
                    company_name=company_name,
                    counterpart_name=counterpart,
                    unread_count=await self.repo.unread_count(thread.chat_thread_uuid, actor.user_uuid),
                    last_message=message_out(last) if last else None,
                )
            )
        return out
