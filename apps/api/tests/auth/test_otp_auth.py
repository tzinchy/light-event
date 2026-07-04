EMAIL = "artem@example.com"


async def request_code(client, email_outbox, email=EMAIL) -> str:
    resp = await client.post("/api/v1/auth/otp/request", json={"email": email})
    assert resp.status_code == 202, resp.text
    sent_to, code = email_outbox.sent[-1]
    assert sent_to == email
    assert len(code) == 6 and code.isdigit()
    return code


async def login(client, email_outbox, email=EMAIL) -> dict:
    code = await request_code(client, email_outbox, email)
    resp = await client.post("/api/v1/auth/otp/verify", json={"email": email, "code": code})
    assert resp.status_code == 200, resp.text
    return resp.json()


def bearer(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_first_login_creates_user_and_returns_tokens(client, email_outbox):
    tokens = await login(client, email_outbox)

    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"] and tokens["refresh_token"]
    assert tokens["is_new_user"] is True

    me = await client.get("/api/v1/auth/me", headers=bearer(tokens))
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == EMAIL
    assert body["email_verified_at"] is not None
    assert body["phone"] is None
    assert body["platform_role"] == "user"
    assert body["pd_consent_at"] is None
    assert body["user_uuid"]


async def test_second_login_reuses_existing_user(client, email_outbox):
    first = await login(client, email_outbox)
    second = await login(client, email_outbox)

    assert second["is_new_user"] is False
    me1 = await client.get("/api/v1/auth/me", headers=bearer(first))
    me2 = await client.get("/api/v1/auth/me", headers=bearer(second))
    assert me1.json()["user_uuid"] == me2.json()["user_uuid"]


async def test_verify_with_wrong_code_fails(client, email_outbox):
    code = await request_code(client, email_outbox)
    wrong = "000000" if code != "000000" else "111111"

    resp = await client.post("/api/v1/auth/otp/verify", json={"email": EMAIL, "code": wrong})
    assert resp.status_code == 401


async def test_verify_without_requested_code_fails(client):
    resp = await client.post("/api/v1/auth/otp/verify", json={"email": EMAIL, "code": "123456"})
    assert resp.status_code == 401


async def test_verify_attempts_are_limited(client, email_outbox, settings):
    code = await request_code(client, email_outbox)
    wrong = "000000" if code != "000000" else "111111"

    for _ in range(settings.otp_verify_max_attempts):
        resp = await client.post("/api/v1/auth/otp/verify", json={"email": EMAIL, "code": wrong})
        assert resp.status_code == 401

    resp = await client.post("/api/v1/auth/otp/verify", json={"email": EMAIL, "code": wrong})
    assert resp.status_code == 429

    # после исчерпания попыток даже верный код недействителен
    resp = await client.post("/api/v1/auth/otp/verify", json={"email": EMAIL, "code": code})
    assert resp.status_code in (401, 429)


async def test_otp_requests_are_rate_limited_per_email(client, email_outbox, settings):
    for _ in range(settings.otp_request_limit):
        resp = await client.post("/api/v1/auth/otp/request", json={"email": EMAIL})
        assert resp.status_code == 202

    resp = await client.post("/api/v1/auth/otp/request", json={"email": EMAIL})
    assert resp.status_code == 429


async def test_invalid_email_format_rejected(client):
    resp = await client.post("/api/v1/auth/otp/request", json={"email": "not-an-email"})
    assert resp.status_code == 422


async def test_me_requires_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


async def test_refresh_rotates_tokens(client, email_outbox):
    tokens = await login(client, email_outbox)

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    fresh = resp.json()
    assert fresh["access_token"] and fresh["refresh_token"]

    # старый refresh одноразовый
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401

    me = await client.get("/api/v1/auth/me", headers=bearer(fresh))
    assert me.status_code == 200


async def test_logout_revokes_refresh_token(client, email_outbox):
    tokens = await login(client, email_outbox)

    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=bearer(tokens),
    )
    assert resp.status_code == 204

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


async def test_consent_sets_timestamp(client, email_outbox):
    tokens = await login(client, email_outbox)

    resp = await client.post("/api/v1/auth/consent", headers=bearer(tokens))
    assert resp.status_code == 200
    assert resp.json()["pd_consent_at"] is not None

    me = await client.get("/api/v1/auth/me", headers=bearer(tokens))
    assert me.json()["pd_consent_at"] is not None
