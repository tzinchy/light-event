async def test_patch_profile_updates_fields(client, login_user):
    session = await login_user()

    resp = await client.patch(
        "/api/v1/users/me",
        json={"name": "Артём Соколов", "city": "Москва", "desired_roles": ["Официант", "Бариста"]},
        headers=session["headers"],
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Артём Соколов"
    assert body["city"] == "Москва"
    assert body["desired_roles"] == ["Официант", "Бариста"]

    me = await client.get("/api/v1/auth/me", headers=session["headers"])
    assert me.json()["name"] == "Артём Соколов"


async def test_partial_patch_keeps_other_fields(client, login_user):
    session = await login_user()
    await client.patch(
        "/api/v1/users/me",
        json={"name": "Артём Соколов", "city": "Москва"},
        headers=session["headers"],
    )

    resp = await client.patch("/api/v1/users/me", json={"city": "Казань"}, headers=session["headers"])

    body = resp.json()
    assert body["city"] == "Казань"
    assert body["name"] == "Артём Соколов"


async def test_desired_roles_must_be_from_catalog(client, login_user):
    session = await login_user()

    resp = await client.patch(
        "/api/v1/users/me",
        json={"desired_roles": ["Космонавт"]},
        headers=session["headers"],
    )

    assert resp.status_code == 422


async def test_patch_requires_auth(client):
    resp = await client.patch("/api/v1/users/me", json={"name": "X"})
    assert resp.status_code == 401
