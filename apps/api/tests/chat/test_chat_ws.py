"""Realtime-чат по WebSocket: доставка сообщения, онлайн-статус, авторизация (PLAN §3.6/§9 п.11).

WS поднимается на реальном uvicorn-сокете; REST-настройка треда идёт через общий стенд
(та же тест-БД/Redis), поэтому доставка проверяется по-настоящему, через Redis pub/sub.
"""

import asyncio
import json
import socket

import pytest
import uvicorn
import websockets

from app.main import create_app
from tests.balance.test_payout import apply_to_vacancy, setup_active_vacancy


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


async def _serve(settings):
    server = uvicorn.Server(
        uvicorn.Config(create_app(settings), host="127.0.0.1", port=_free_port(), log_level="warning")
    )
    task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    return server, task, f"ws://127.0.0.1:{port}/api/v1/chat/ws"


async def _recv_of_type(ws, wanted: str, timeout: float = 5.0) -> dict:
    async with asyncio.timeout(timeout):
        while True:
            data = json.loads(await ws.recv())
            if data.get("type") == wanted:
                return data


async def test_ws_delivers_message_and_online_presence(client, login_user, make_admin, settings):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790577700")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79057770013")
    thread = (
        await client.post(
            "/api/v1/chat/threads",
            json={"application_uuid": worker["application_uuid"]},
            headers=worker["headers"],
        )
    ).json()["chat_thread_uuid"]

    server, task, base = await _serve(settings)
    try:
        wt = worker["tokens"]["access_token"]
        ot = ctx["owner"]["tokens"]["access_token"]

        async with websockets.connect(f"{base}?token={wt}") as ws_worker:
            await asyncio.sleep(0.3)  # дать подписке на Redis-канал установиться
            async with websockets.connect(f"{base}?token={ot}") as ws_owner:
                # соискатель видит, что организатор вышел онлайн
                presence = await _recv_of_type(ws_worker, "presence")
                assert presence["user_uuid"] == ctx["owner"]["me"]["user_uuid"]
                assert presence["online"] is True

                # сообщение организатора доходит соискателю в реальном времени
                await ws_owner.send(
                    json.dumps({"type": "send", "chat_thread_uuid": thread, "text": "Готовы к смене?"})
                )
                message = await _recv_of_type(ws_worker, "message")
                assert message["text"] == "Готовы к смене?"
                assert message["chat_thread_uuid"] == thread

        # сообщение сохранено — видно в REST-истории
        history = (
            await client.get(f"/api/v1/chat/threads/{thread}/messages", headers=worker["headers"])
        ).json()
        assert [m["text"] for m in history] == ["Готовы к смене?"]
    finally:
        server.should_exit = True
        await task


async def test_ws_rejects_bad_token(settings):
    server, task, base = await _serve(settings)
    try:
        with pytest.raises(websockets.exceptions.InvalidStatus):
            async with websockets.connect(f"{base}?token=garbage"):
                pass
    finally:
        server.should_exit = True
        await task
