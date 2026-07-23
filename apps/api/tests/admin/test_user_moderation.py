"""Админская модерация пользователей + управление (PLAN §11.15).

Флоу: юзер грузит документ → админ смотрит → approve / resubmit / ban / unban.
Плюс список всех пользователей, правка роли, ручное создание.
"""

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-image-payload" * 10


async def upload(client, headers, kind="passport"):
    return await client.post(
        "/api/v1/documents",
        data={"kind": kind},
        files={"file": (f"{kind}.png", PNG_BYTES, "image/png")},
        headers=headers,
    )


async def test_user_endpoints_require_admin(client, login_user):
    user = await login_user("+79061110001")

    assert (await client.get("/api/v1/admin/users")).status_code == 401
    assert (await client.get("/api/v1/admin/users", headers=user["headers"])).status_code == 403
    missing = "019f0000-0000-7000-8000-000000000000"
    assert (
        await client.post(f"/api/v1/admin/users/{missing}/approve", headers=user["headers"])
    ).status_code == 403


async def test_admin_lists_all_users(client, login_user, make_admin):
    u1 = await login_user("+79061110002")
    u2 = await login_user("+79061110003")
    admin = await login_user("+79061110004")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.get("/api/v1/admin/users", headers=admin["headers"])

    assert resp.status_code == 200, resp.text
    by_uuid = {u["user_uuid"]: u for u in resp.json()}
    assert u1["me"]["user_uuid"] in by_uuid
    assert u2["me"]["user_uuid"] in by_uuid
    assert by_uuid[u1["me"]["user_uuid"]]["moderation_status"] == "pending"


async def test_admin_filters_by_moderation_status(client, login_user, make_admin):
    u1 = await login_user("+79061110005")
    admin = await login_user("+79061110006")
    await make_admin(admin["me"]["user_uuid"])
    await client.post(f"/api/v1/admin/users/{u1['me']['user_uuid']}/approve", headers=admin["headers"])

    pending = await client.get("/api/v1/admin/users?status=pending", headers=admin["headers"])
    approved = await client.get("/api/v1/admin/users?status=approved", headers=admin["headers"])

    assert u1["me"]["user_uuid"] not in {u["user_uuid"] for u in pending.json()}
    assert u1["me"]["user_uuid"] in {u["user_uuid"] for u in approved.json()}


async def test_detail_shows_documents(client, login_user, make_admin):
    owner = await login_user("+79061110007")
    admin = await login_user("+79061110008")
    await make_admin(admin["me"]["user_uuid"])
    await upload(client, owner["headers"], kind="passport")

    resp = await client.get(f"/api/v1/admin/users/{owner['me']['user_uuid']}", headers=admin["headers"])

    assert resp.status_code == 200, resp.text
    body = resp.json()
    kinds = {d["kind"] for d in body["documents"]}
    assert "passport" in kinds
    assert body["documents"][0]["status"] == "pending"


async def test_approve_sets_status(client, login_user, make_admin):
    owner = await login_user("+79061110009")
    admin = await login_user("+79061110010")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.post(f"/api/v1/admin/users/{owner['me']['user_uuid']}/approve", headers=admin["headers"])

    assert resp.status_code == 200, resp.text
    assert resp.json()["moderation_status"] == "approved"


async def test_resubmit_with_reason(client, login_user, make_admin):
    owner = await login_user("+79061110011")
    admin = await login_user("+79061110012")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.post(
        f"/api/v1/admin/users/{owner['me']['user_uuid']}/resubmit",
        json={"reason": "Паспорт нечитаемый — переснимите"},
        headers=admin["headers"],
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["moderation_status"] == "resubmit"
    assert resp.json()["moderation_reason"] == "Паспорт нечитаемый — переснимите"
    # юзер всё ещё может войти, чтобы дослать документ
    assert (await client.get("/api/v1/auth/me", headers=owner["headers"])).status_code == 200


async def test_ban_locks_out_user(client, login_user, make_admin):
    owner = await login_user("+79061110013")
    admin = await login_user("+79061110014")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.post(
        f"/api/v1/admin/users/{owner['me']['user_uuid']}/ban",
        json={"reason": "Поддельные документы"},
        headers=admin["headers"],
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["moderation_status"] == "banned"
    # забаненный не проходит ни на один авторизованный эндпоинт
    assert (await client.get("/api/v1/auth/me", headers=owner["headers"])).status_code == 401


async def test_unban_restores_access(client, login_user, make_admin):
    owner = await login_user("+79061110015")
    admin = await login_user("+79061110016")
    await make_admin(admin["me"]["user_uuid"])
    await client.post(f"/api/v1/admin/users/{owner['me']['user_uuid']}/ban", json={"reason": "спам"}, headers=admin["headers"])

    resp = await client.post(f"/api/v1/admin/users/{owner['me']['user_uuid']}/unban", headers=admin["headers"])

    assert resp.status_code == 200, resp.text
    assert resp.json()["moderation_status"] == "approved"
    assert (await client.get("/api/v1/auth/me", headers=owner["headers"])).status_code == 200


async def test_patch_changes_role(client, login_user, make_admin):
    owner = await login_user("+79061110017")
    admin = await login_user("+79061110018")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.patch(
        f"/api/v1/admin/users/{owner['me']['user_uuid']}",
        json={"platform_role": "vip_user"},
        headers=admin["headers"],
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["platform_role"] == "vip_user"


async def test_admin_cannot_change_own_role(client, login_user, make_admin):
    admin = await login_user("+79061110019")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.patch(
        f"/api/v1/admin/users/{admin['me']['user_uuid']}",
        json={"platform_role": "user"},
        headers=admin["headers"],
    )

    assert resp.status_code == 400, resp.text


async def test_admin_cannot_ban_self(client, login_user, make_admin):
    admin = await login_user("+79061110020")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.post(
        f"/api/v1/admin/users/{admin['me']['user_uuid']}/ban", json={"reason": "спам"}, headers=admin["headers"]
    )

    assert resp.status_code == 400, resp.text


async def test_admin_creates_user(client, login_user, make_admin):
    admin = await login_user("+79061110021")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.post(
        "/api/v1/admin/users",
        json={"email": "new-hire@example.com", "platform_role": "vip_user"},
        headers=admin["headers"],
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "new-hire@example.com"
    assert body["platform_role"] == "vip_user"
    assert body["moderation_status"] == "approved"

    listed = await client.get("/api/v1/admin/users", headers=admin["headers"])
    assert "new-hire@example.com" in {u["email"] for u in listed.json()}


async def test_admin_create_rejects_duplicate_email(client, login_user, make_admin):
    existing = await login_user("dup@example.com")
    admin = await login_user("+79061110022")
    await make_admin(admin["me"]["user_uuid"])
    assert existing["me"]["email"] == "dup@example.com"

    resp = await client.post(
        "/api/v1/admin/users",
        json={"email": "dup@example.com", "platform_role": "user"},
        headers=admin["headers"],
    )

    assert resp.status_code == 409, resp.text
