"""Избранные компании + уведомление подписчику о новой смене (PLAN §11.8)."""

from tests.vacancy.test_vacancy import create_draft, fund_company, moderate, publish, setup_company


async def _company_with_funds(client, login_user, make_admin, base_phone: str) -> dict:
    ctx = await setup_company(client, login_user, base_phone + "1")
    await fund_company(client, login_user, make_admin, ctx, base_phone + "2", amount_kop=1_000_000)
    return ctx


async def _publish_vacancy(client, ctx) -> str:
    vacancy = await create_draft(client, ctx)
    await publish(client, ctx, vacancy["vacancy_uuid"])
    await moderate(client, ctx, vacancy["vacancy_uuid"], "approve")
    return vacancy["vacancy_uuid"]


async def _notifications(client, headers) -> dict:
    return (await client.get("/api/v1/notifications", headers=headers)).json()


async def test_favorite_toggle_and_list(client, login_user, make_admin):
    ctx = await _company_with_funds(client, login_user, make_admin, "+790583300")
    worker = await login_user("+79058330103")
    company_uuid = ctx["company_uuid"]

    assert (
        await client.post(f"/api/v1/companies/{company_uuid}/favorite", headers=worker["headers"])
    ).status_code == 201
    favs = (await client.get("/api/v1/favorites/companies", headers=worker["headers"])).json()
    assert [f["company_uuid"] for f in favs] == [company_uuid]

    # повторное добавление идемпотентно
    assert (
        await client.post(f"/api/v1/companies/{company_uuid}/favorite", headers=worker["headers"])
    ).status_code == 201

    assert (
        await client.delete(f"/api/v1/companies/{company_uuid}/favorite", headers=worker["headers"])
    ).status_code == 204
    assert (await client.get("/api/v1/favorites/companies", headers=worker["headers"])).json() == []


async def test_follower_notified_on_new_vacancy(client, login_user, make_admin):
    ctx = await _company_with_funds(client, login_user, make_admin, "+790583310")
    worker = await login_user("+79058331003")
    await client.post(f"/api/v1/companies/{ctx['company_uuid']}/favorite", headers=worker["headers"])

    assert (await _notifications(client, worker["headers"]))["unread"] == 0

    vacancy_uuid = await _publish_vacancy(client, ctx)

    notifs = await _notifications(client, worker["headers"])
    assert notifs["unread"] == 1
    assert notifs["items"][0]["vacancy_uuid"] == vacancy_uuid

    assert (await client.post("/api/v1/notifications/read", headers=worker["headers"])).status_code == 200
    assert (await _notifications(client, worker["headers"]))["unread"] == 0


async def test_non_follower_gets_no_notification(client, login_user, make_admin):
    ctx = await _company_with_funds(client, login_user, make_admin, "+790583320")
    stranger = await login_user("+79058332003")  # не подписан

    await _publish_vacancy(client, ctx)

    assert (await _notifications(client, stranger["headers"]))["unread"] == 0


async def test_favorite_requires_auth(client, login_user, make_admin):
    ctx = await _company_with_funds(client, login_user, make_admin, "+790583330")
    assert (await client.post(f"/api/v1/companies/{ctx['company_uuid']}/favorite")).status_code == 401
    assert (await client.get("/api/v1/notifications")).status_code == 401
