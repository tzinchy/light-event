import asyncio
import json
import logging
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Response, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.repo import ChatRepo
from app.chat.schemas import MessageOut, MessageSendIn, ThreadOpenIn, ThreadOut
from app.chat.service import ChatService
from app.core.deps import get_current_user, get_session
from app.core.errors import DomainError
from app.core.security import decode_access_token
from app.user.models import User
from app.user.repo import UserRepo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

ONLINE_TTL_SEC = 60


def _user_channel(user_uuid: UUID) -> str:
    return f"chat:user:{user_uuid}"


def _online_key(user_uuid: UUID) -> str:
    return f"chat:online:{user_uuid}"


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


async def _publish(redis, user_uuids, payload: dict) -> None:
    data = json.dumps(payload)
    for uid in user_uuids:
        await redis.publish(_user_channel(uid), data)


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    """Realtime-чат: авторизация по токену (?token=), приём send/read, онлайн-статус.

    Доставка — через Redis pub/sub по каналу на пользователя, поэтому переживает
    несколько воркеров API (PLAN §3.6): каждое соединение слушает свой канал.
    """
    state = websocket.app.state
    try:
        user_uuid = decode_access_token(websocket.query_params.get("token", ""), state.settings.app_secret_key)
    except jwt.InvalidTokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    async with state.session_factory() as session:
        user = await UserRepo(session).get(user_uuid)
        if user is None or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        counterparts = await ChatRepo(session).counterpart_uuids(user_uuid)

    await websocket.accept()
    redis = state.redis
    await redis.set(_online_key(user_uuid), "1", ex=ONLINE_TTL_SEC)
    await _publish(redis, counterparts, {"type": "presence", "user_uuid": str(user_uuid), "online": True})

    pubsub = redis.pubsub()
    await pubsub.subscribe(_user_channel(user_uuid))

    async def pump_out() -> None:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])

    out_task = asyncio.create_task(pump_out())
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("type")
            if action == "send":
                async with state.session_factory() as session:
                    async with session.begin():
                        message = await ChatService(session).send(
                            user, UUID(data["chat_thread_uuid"]), MessageSendIn(text=data["text"])
                        )
                        participants = await ChatRepo(session).thread_participant_uuids(message.chat_thread_uuid)
                        payload = {"type": "message", **MessageOut.model_validate(message).model_dump(mode="json")}
                await _publish(redis, participants, payload)
            elif action == "read":
                thread_uuid = UUID(data["chat_thread_uuid"])
                async with state.session_factory() as session:
                    async with session.begin():
                        await ChatService(session).mark_read(user, thread_uuid)
                        participants = await ChatRepo(session).thread_participant_uuids(thread_uuid)
                await _publish(
                    redis,
                    participants,
                    {"type": "read", "chat_thread_uuid": str(thread_uuid), "reader_uuid": str(user_uuid)},
                )
            elif action == "ping":
                await redis.expire(_online_key(user_uuid), ONLINE_TTL_SEC)
    except WebSocketDisconnect:
        pass
    except DomainError as exc:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=exc.detail[:120])
    finally:
        out_task.cancel()
        await pubsub.unsubscribe(_user_channel(user_uuid))
        await pubsub.aclose()
        await redis.delete(_online_key(user_uuid))
        await _publish(redis, counterparts, {"type": "presence", "user_uuid": str(user_uuid), "online": False})
