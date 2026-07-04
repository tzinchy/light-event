"""Чат по заявке (PLAN §3.6): тред соискатель ↔ команда компании, непрочитанные, доступ."""

from tests.balance.test_payout import apply_to_vacancy, setup_active_vacancy


async def open_thread(client, headers, application_uuid: str):
    return await client.post(
        "/api/v1/chat/threads", json={"application_uuid": application_uuid}, headers=headers
    )


async def send(client, headers, thread_uuid: str, text: str):
    return await client.post(
        f"/api/v1/chat/threads/{thread_uuid}/messages", json={"text": text}, headers=headers
    )


async def test_thread_created_once_per_application(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790599900")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79059990013")

    resp = await open_thread(client, worker["headers"], worker["application_uuid"])
    assert resp.status_code == 201, resp.text
    thread_uuid = resp.json()["chat_thread_uuid"]

    # повторное открытие возвращает тот же тред (не дубль)
    resp = await open_thread(client, ctx["owner"]["headers"], worker["application_uuid"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["chat_thread_uuid"] == thread_uuid


async def test_messages_flow_and_unread_counters(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790599910")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79059991013")
    thread_uuid = (await open_thread(client, worker["headers"], worker["application_uuid"])).json()[
        "chat_thread_uuid"
    ]

    assert (await send(client, worker["headers"], thread_uuid, "Здравствуйте! Подскажите дресс-код")).status_code == 201
    assert (await send(client, ctx["owner"]["headers"], thread_uuid, "Чёрный верх / низ")).status_code == 201

    # у соискателя один непрочитанный (ответ организации)
    threads = (await client.get("/api/v1/chat/threads", headers=worker["headers"])).json()
    assert len(threads) == 1
    assert threads[0]["chat_thread_uuid"] == thread_uuid
    assert threads[0]["unread_count"] == 1
    assert threads[0]["last_message"]["text"] == "Чёрный верх / низ"

    # история в хронологическом порядке; чтение помечает входящие
    messages = (
        await client.get(f"/api/v1/chat/threads/{thread_uuid}/messages", headers=worker["headers"])
    ).json()
    assert [m["text"] for m in messages] == ["Здравствуйте! Подскажите дресс-код", "Чёрный верх / низ"]

    assert (
        await client.post(f"/api/v1/chat/threads/{thread_uuid}/read", headers=worker["headers"])
    ).status_code == 200
    threads = (await client.get("/api/v1/chat/threads", headers=worker["headers"])).json()
    assert threads[0]["unread_count"] == 0

    # у организации непрочитанным остаётся первый вопрос соискателя
    org_threads = (await client.get("/api/v1/chat/threads", headers=ctx["owner"]["headers"])).json()
    assert org_threads[0]["unread_count"] == 1


async def test_outsider_cannot_access_thread(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790599920")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79059992013")
    thread_uuid = (await open_thread(client, worker["headers"], worker["application_uuid"])).json()[
        "chat_thread_uuid"
    ]
    outsider = await login_user("+79059992019")

    assert (await open_thread(client, outsider["headers"], worker["application_uuid"])).status_code == 403
    assert (
        await client.get(f"/api/v1/chat/threads/{thread_uuid}/messages", headers=outsider["headers"])
    ).status_code == 403
    assert (await send(client, outsider["headers"], thread_uuid, "привет")).status_code == 403
    assert (await client.get("/api/v1/chat/threads")).status_code == 401


async def test_empty_text_rejected(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790599930")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79059993013")
    thread_uuid = (await open_thread(client, worker["headers"], worker["application_uuid"])).json()[
        "chat_thread_uuid"
    ]

    assert (await send(client, worker["headers"], thread_uuid, "")).status_code == 422
    assert (await send(client, worker["headers"], thread_uuid, "  ")).status_code == 422
