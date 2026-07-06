"""Опыт работы в профиле + публичный профиль соискателя без контактов (PLAN §3.1)."""


async def test_experience_saved_and_validated(client, login_user):
    session = await login_user("+79051239001")

    ok = await client.patch(
        "/api/v1/users/me", json={"experience": "y1_3"}, headers=session["headers"]
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["experience"] == "y1_3"

    bad = await client.patch(
        "/api/v1/users/me", json={"experience": "ветеран"}, headers=session["headers"]
    )
    assert bad.status_code == 422


async def test_public_worker_profile_hides_contacts(client, login_user):
    worker = await login_user("+79051239002")
    await client.patch(
        "/api/v1/users/me",
        json={"name": "Артём Соколов", "city": "Москва", "experience": "y3_6"},
        headers=worker["headers"],
    )
    viewer = await login_user("+79051239003")

    resp = await client.get(
        f"/api/v1/users/{worker['me']['user_uuid']}/public", headers=viewer["headers"]
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Артём Соколов"
    assert body["city"] == "Москва"
    assert body["experience"] == "y3_6"
    # контактов нет — организация не может связаться в обход платформы
    assert "phone" not in body
    assert "email" not in body

    assert (await client.get(f"/api/v1/users/{worker['me']['user_uuid']}/public")).status_code == 401
