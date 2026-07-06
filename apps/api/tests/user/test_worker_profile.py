"""Профиль соискателя: приватность по отклику, опыт/анкета, телеграм (PLAN §3.1, §11.12)."""

from tests.balance.test_payout import apply_to_vacancy, setup_active_vacancy


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


async def test_profile_visible_only_after_application(client, login_user, make_admin):
    """Профиль не публичный: сам/админ/команда компании с откликом — остальным 403 (§11.12)."""
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790586100")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79058610013")
    await client.patch(
        "/api/v1/users/me",
        json={"name": "Артём Соколов", "gender": "male", "citizenship": "РФ", "birth_date": "1998-05-20"},
        headers=worker["headers"],
    )
    target = worker["me"]["user_uuid"]

    # команда компании, куда откликнулся — видит (без контактов)
    resp = await client.get(f"/api/v1/users/{target}/public", headers=ctx["owner"]["headers"])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["gender"] == "male"
    assert body["citizenship"] == "РФ"
    assert body["birth_date"] == "1998-05-20"
    assert "phone" not in body and "email" not in body and "telegram" not in body

    # сам и админ — видят
    assert (await client.get(f"/api/v1/users/{target}/public", headers=worker["headers"])).status_code == 200
    assert (
        await client.get(f"/api/v1/users/{target}/public", headers=ctx["admin"]["headers"])
    ).status_code == 200

    # посторонний пользователь и посторонняя организация — 403
    stranger = await login_user("+79058610099")
    assert (await client.get(f"/api/v1/users/{target}/public", headers=stranger["headers"])).status_code == 403
    other_org = await setup_active_vacancy(client, login_user, make_admin, "+790586200")
    assert (
        await client.get(f"/api/v1/users/{target}/public", headers=other_org["owner"]["headers"])
    ).status_code == 403

    # без токена — 401
    assert (await client.get(f"/api/v1/users/{target}/public")).status_code == 401


async def test_telegram_and_new_fields_editable(client, login_user):
    session = await login_user("+79051239005")

    resp = await client.patch(
        "/api/v1/users/me", json={"telegram": "@artem_sokolov"}, headers=session["headers"]
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["telegram"] == "artem_sokolov"  # нормализован без @

    # редактирование тега
    resp = await client.patch(
        "/api/v1/users/me", json={"telegram": "sokolov_new"}, headers=session["headers"]
    )
    assert resp.json()["telegram"] == "sokolov_new"

    # невалидные значения отклоняются
    assert (
        await client.patch("/api/v1/users/me", json={"telegram": "a b!"}, headers=session["headers"])
    ).status_code == 422
    assert (
        await client.patch("/api/v1/users/me", json={"gender": "другое"}, headers=session["headers"])
    ).status_code == 422
    assert (
        await client.patch(
            "/api/v1/users/me", json={"birth_date": "2100-01-01"}, headers=session["headers"]
        )
    ).status_code == 422
