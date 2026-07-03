"""Подтверждение email кодом. Телефон остаётся логином; почта — поле профиля (PLAN §10.2)."""


async def request_email_code(client, headers, email="owner@example.com"):
    return await client.post("/api/v1/users/me/email", json={"email": email}, headers=headers)


async def test_email_code_sent_and_confirmed(client, login_user, email_outbox):
    session = await login_user("+79055550001")

    resp = await request_email_code(client, session["headers"])
    assert resp.status_code == 202, resp.text
    assert len(email_outbox.sent) == 1
    to, code = email_outbox.sent[0]
    assert to == "owner@example.com"
    assert len(code) == 6

    resp = await client.post(
        "/api/v1/users/me/email/confirm", json={"code": code}, headers=session["headers"]
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == "owner@example.com"
    assert body["email_verified_at"] is not None

    me = await client.get("/api/v1/users/me", headers=session["headers"])
    assert me.json()["email_verified_at"] is not None


async def test_wrong_code_rejected(client, login_user, email_outbox):
    session = await login_user("+79055550002")
    await request_email_code(client, session["headers"])
    _, code = email_outbox.sent[0]
    wrong = "000000" if code != "000000" else "111111"

    resp = await client.post(
        "/api/v1/users/me/email/confirm", json={"code": wrong}, headers=session["headers"]
    )

    assert resp.status_code == 401
    me = await client.get("/api/v1/users/me", headers=session["headers"])
    assert me.json()["email_verified_at"] is None


async def test_confirm_without_request_rejected(client, login_user):
    session = await login_user("+79055550003")

    resp = await client.post(
        "/api/v1/users/me/email/confirm", json={"code": "123456"}, headers=session["headers"]
    )

    assert resp.status_code == 401


async def test_email_request_rate_limited(client, login_user, email_outbox):
    session = await login_user("+79055550004")

    statuses = [
        (await request_email_code(client, session["headers"])).status_code for _ in range(4)
    ]

    assert statuses[:3] == [202, 202, 202]
    assert statuses[3] == 429


async def test_changing_email_resets_verification(client, login_user, email_outbox):
    session = await login_user("+79055550005")
    await request_email_code(client, session["headers"])
    _, code = email_outbox.sent[0]
    await client.post("/api/v1/users/me/email/confirm", json={"code": code}, headers=session["headers"])

    resp = await request_email_code(client, session["headers"], email="new@example.com")
    assert resp.status_code == 202

    me = await client.get("/api/v1/users/me", headers=session["headers"])
    assert me.json()["email"] == "new@example.com"
    assert me.json()["email_verified_at"] is None


async def test_invalid_email_rejected(client, login_user):
    session = await login_user("+79055550006")

    resp = await request_email_code(client, session["headers"], email="не-почта")

    assert resp.status_code == 422


async def test_email_endpoints_require_auth(client):
    assert (await client.post("/api/v1/users/me/email", json={"email": "a@b.ru"})).status_code == 401
    assert (
        await client.post("/api/v1/users/me/email/confirm", json={"code": "123456"})
    ).status_code == 401
