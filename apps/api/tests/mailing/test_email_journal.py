"""§11.14: журнал исходящих писем + отправка письма админом."""

import pytest


async def test_otp_request_logged_in_journal(client, login_user, make_admin):
    """Запрос OTP оставляет запись kind=otp/status=sent, видимую админу в журнале."""
    await client.post("/api/v1/auth/otp/request", json={"email": "worker@example.com"})

    admin = await login_user("admin@example.com")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.get("/api/v1/admin/emails", headers=admin["headers"])
    assert resp.status_code == 200, resp.text
    letters = resp.json()
    otp_letters = [m for m in letters if m["to_email"] == "worker@example.com"]
    assert len(otp_letters) == 1
    letter = otp_letters[0]
    assert letter["kind"] == "otp"
    assert letter["status"] == "sent"
    assert "код подтверждения" in letter["subject"]
    assert letter["created_by"] is None
    # тело с кодом в списке не отдаём наружу целиком? — отдаём: журнал только для админа
    assert letter["body"]


async def test_journal_requires_admin(client, login_user):
    user = await login_user("mortal@example.com")
    resp = await client.get("/api/v1/admin/emails", headers=user["headers"])
    assert resp.status_code == 403


async def test_admin_sends_custom_email(client, login_user, make_admin, email_outbox):
    admin = await login_user("admin@example.com")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.post(
        "/api/v1/admin/emails/send",
        json={"to_email": "guest@example.com", "subject": "Добро пожаловать", "body": "Ждём вас на смене."},
        headers=admin["headers"],
    )
    assert resp.status_code == 201, resp.text
    letter = resp.json()
    assert letter["kind"] == "admin"
    assert letter["status"] == "sent"
    assert letter["to_email"] == "guest@example.com"
    assert letter["created_by"] == admin["me"]["user_uuid"]

    # письмо реально ушло через провайдера
    assert email_outbox.messages[-1] == ("guest@example.com", "Добро пожаловать", "Ждём вас на смене.")

    # и попало в журнал
    resp = await client.get("/api/v1/admin/emails", headers=admin["headers"])
    sent = [m for m in resp.json() if m["to_email"] == "guest@example.com"]
    assert len(sent) == 1


async def test_admin_send_validation(client, login_user, make_admin):
    admin = await login_user("admin@example.com")
    await make_admin(admin["me"]["user_uuid"])
    resp = await client.post(
        "/api/v1/admin/emails/send",
        json={"to_email": "not-an-email", "subject": "", "body": ""},
        headers=admin["headers"],
    )
    assert resp.status_code == 422


async def test_failed_send_recorded_and_returns_502(client, login_user, make_admin, email_outbox):
    admin = await login_user("admin@example.com")
    await make_admin(admin["me"]["user_uuid"])
    email_outbox.fail_next = True

    resp = await client.post(
        "/api/v1/admin/emails/send",
        json={"to_email": "guest@example.com", "subject": "Тест", "body": "Тело"},
        headers=admin["headers"],
    )
    assert resp.status_code == 502

    resp = await client.get("/api/v1/admin/emails", headers=admin["headers"])
    failed = [m for m in resp.json() if m["to_email"] == "guest@example.com"]
    assert len(failed) == 1
    assert failed[0]["status"] == "failed"
    assert failed[0]["error"]


async def test_journal_pagination(client, login_user, make_admin):
    admin = await login_user("admin@example.com")
    await make_admin(admin["me"]["user_uuid"])
    for i in range(3):
        await client.post(
            "/api/v1/admin/emails/send",
            json={"to_email": f"p{i}@example.com", "subject": f"Письмо {i}", "body": "…"},
            headers=admin["headers"],
        )

    resp = await client.get("/api/v1/admin/emails?limit=2", headers=admin["headers"])
    assert len(resp.json()) == 2
    # новые сверху
    assert resp.json()[0]["to_email"] == "p2@example.com"

    resp = await client.get("/api/v1/admin/emails?limit=2&offset=2", headers=admin["headers"])
    assert resp.json()[0]["to_email"] == "p0@example.com"
