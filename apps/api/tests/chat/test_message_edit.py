"""Правка/удаление сообщений: пометки, ревизии для админа, скрытие удалённого (PLAN §11.11)."""

from tests.balance.test_payout import apply_to_vacancy, setup_active_vacancy
from tests.chat.test_chat import open_thread, send


async def _setup_dialog(client, login_user, make_admin, base_phone: str) -> tuple[dict, dict, str]:
    ctx = await setup_active_vacancy(client, login_user, make_admin, base_phone)
    worker = await apply_to_vacancy(client, login_user, ctx, base_phone + "13")
    thread = (await open_thread(client, worker["headers"], worker["application_uuid"])).json()[
        "chat_thread_uuid"
    ]
    return ctx, worker, thread


async def test_edit_sets_mark_and_stores_revision_for_admin(client, login_user, make_admin):
    ctx, worker, thread = await _setup_dialog(client, login_user, make_admin, "+790585100")
    message = (await send(client, worker["headers"], thread, "Здравствуйте!")).json()

    resp = await client.patch(
        f"/api/v1/chat/messages/{message['chat_message_uuid']}",
        json={"text": "Здравствуйте! Подскажите дресс-код"},
        headers=worker["headers"],
    )
    assert resp.status_code == 200, resp.text
    edited = resp.json()
    assert edited["text"] == "Здравствуйте! Подскажите дресс-код"
    assert edited["edited_at"] is not None  # пометка «изменено»

    # чужой не может править
    assert (
        await client.patch(
            f"/api/v1/chat/messages/{message['chat_message_uuid']}",
            json={"text": "hack"},
            headers=ctx["owner"]["headers"],
        )
    ).status_code == 403

    # админ видит прежнюю версию
    moderated = (
        await client.get("/api/v1/chat/admin/moderated-messages", headers=ctx["admin"]["headers"])
    ).json()
    row = next(m for m in moderated if m["chat_message_uuid"] == message["chat_message_uuid"])
    assert [r["text"] for r in row["revisions"]] == ["Здравствуйте!"]

    # обычному пользователю админ-выдача недоступна
    assert (
        await client.get("/api/v1/chat/admin/moderated-messages", headers=worker["headers"])
    ).status_code == 403


async def test_delete_flags_and_hides_text_but_admin_sees_original(client, login_user, make_admin):
    ctx, worker, thread = await _setup_dialog(client, login_user, make_admin, "+790585200")
    message = (await send(client, worker["headers"], thread, "Секретный текст")).json()

    resp = await client.delete(
        f"/api/v1/chat/messages/{message['chat_message_uuid']}", headers=worker["headers"]
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["deleted_at"] is not None

    # в истории сообщение остаётся, но текст скрыт
    history = (
        await client.get(f"/api/v1/chat/threads/{thread}/messages", headers=ctx["owner"]["headers"])
    ).json()
    row = next(m for m in history if m["chat_message_uuid"] == message["chat_message_uuid"])
    assert row["deleted_at"] is not None
    assert row["text"] == ""

    # удалённое нельзя редактировать
    assert (
        await client.patch(
            f"/api/v1/chat/messages/{message['chat_message_uuid']}",
            json={"text": "верни"},
            headers=worker["headers"],
        )
    ).status_code == 409

    # админ видит оригинальный текст удалённого
    moderated = (
        await client.get("/api/v1/chat/admin/moderated-messages", headers=ctx["admin"]["headers"])
    ).json()
    row = next(m for m in moderated if m["chat_message_uuid"] == message["chat_message_uuid"])
    assert row["text"] == "Секретный текст"


async def test_profile_extra_fields(client, login_user):
    session = await login_user("+79058530001")
    resp = await client.patch(
        "/api/v1/users/me",
        json={"about": "Официант с опытом банкетов", "english_level": "intermediate", "education": "higher"},
        headers=session["headers"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["about"] == "Официант с опытом банкетов"
    assert body["english_level"] == "intermediate"
    assert body["education"] == "higher"

    assert (
        await client.patch(
            "/api/v1/users/me", json={"english_level": "native??"}, headers=session["headers"]
        )
    ).status_code == 422

    # публичный профиль отдаёт новые поля (по-прежнему без контактов)
    viewer = await login_user("+79058530002")
    pub = (
        await client.get(f"/api/v1/users/{session['me']['user_uuid']}/public", headers=viewer["headers"])
    ).json()
    assert pub["about"] == "Официант с опытом банкетов"
    assert pub["english_level"] == "intermediate"
    assert pub["education"] == "higher"
    assert "email" not in pub
