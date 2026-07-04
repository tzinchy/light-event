from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.schemas import MessageOut, MessageSendIn, ThreadOpenIn, ThreadOut
from app.chat.service import ChatService
from app.core.deps import get_current_user, get_session
from app.user.models import User

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def get_chat_service(session: AsyncSession = Depends(get_session)) -> ChatService:
    return ChatService(session=session)


@router.post("/threads", response_model=dict)
async def open_thread(
    payload: ThreadOpenIn,
    response: Response,
    actor: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> dict:
    thread, created = await service.open_thread(actor, payload.application_uuid)
    response.status_code = 201 if created else 200
    return {"chat_thread_uuid": str(thread.chat_thread_uuid)}


@router.get("/threads", response_model=list[ThreadOut])
async def my_threads(
    actor: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> list[ThreadOut]:
    return await service.list_threads(actor)


@router.get("/threads/{chat_thread_uuid}/messages", response_model=list[MessageOut])
async def thread_messages(
    chat_thread_uuid: UUID,
    actor: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> list[MessageOut]:
    return [MessageOut.model_validate(m) for m in await service.list_messages(actor, chat_thread_uuid)]


@router.post("/threads/{chat_thread_uuid}/messages", response_model=MessageOut, status_code=201)
async def send_message(
    chat_thread_uuid: UUID,
    payload: MessageSendIn,
    actor: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> MessageOut:
    return MessageOut.model_validate(await service.send(actor, chat_thread_uuid, payload))


@router.post("/threads/{chat_thread_uuid}/read")
async def mark_read(
    chat_thread_uuid: UUID,
    actor: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> dict:
    await service.mark_read(actor, chat_thread_uuid)
    return {"ok": True}
