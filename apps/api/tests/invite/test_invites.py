from tests.helpers import create_verified_company

async def setup_company(client, login_user, phone: str) -> dict:
    owner = await login_user(phone)
    company = await create_verified_company(client, owner["headers"])
    return {"owner": owner, "company_uuid": company["company_uuid"]}


async def create_invite(client, headers, company_uuid, role="manager", expires_in="7d", max_uses=5):
    return await client.post(
        f"/api/v1/companies/{company_uuid}/invites",
        json={"role": role, "expires_in": expires_in, "max_uses": max_uses},
        headers=headers,
    )


async def test_invite_created_by_main_manager_and_permission_holder(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, "+79051250001")
    inviter = await login_user("+79051250002")
    no_perm = await login_user("+79051250003")
    await add_team_member(ctx["company_uuid"], inviter["me"]["user_uuid"], role="manager", perm_invite=True)
    await add_team_member(ctx["company_uuid"], no_perm["me"]["user_uuid"], role="manager")

    resp = await create_invite(client, ctx["owner"]["headers"], ctx["company_uuid"])
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["code"]
    assert body["role"] == "manager"
    assert body["max_uses"] == 5
    assert body["uses_count"] == 0
    assert body["active"] is True

    assert (await create_invite(client, inviter["headers"], ctx["company_uuid"])).status_code == 201
    assert (await create_invite(client, no_perm["headers"], ctx["company_uuid"])).status_code == 403


async def test_invite_cannot_grant_main_manager_role(client, login_user):
    ctx = await setup_company(client, login_user, "+79051250010")

    resp = await create_invite(client, ctx["owner"]["headers"], ctx["company_uuid"], role="main_manager")
    assert resp.status_code == 422


async def test_accept_invite_joins_team_and_counts_use(client, login_user):
    ctx = await setup_company(client, login_user, "+79051250020")
    newcomer = await login_user("+79051250021")
    code = (await create_invite(client, ctx["owner"]["headers"], ctx["company_uuid"], role="coordinator")).json()["code"]

    resp = await client.post(f"/api/v1/invites/{code}/accept", headers=newcomer["headers"])
    assert resp.status_code == 201, resp.text
    member = resp.json()
    assert member["company_role"] == "coordinator"
    assert member["user_uuid"] == newcomer["me"]["user_uuid"]
    assert not member["perm_create"]  # права выдаёт main_manager после вступления

    invites = (await client.get(f"/api/v1/companies/{ctx['company_uuid']}/invites", headers=ctx["owner"]["headers"])).json()
    assert invites[0]["uses_count"] == 1

    # повторное вступление того же пользователя
    resp = await client.post(f"/api/v1/invites/{code}/accept", headers=newcomer["headers"])
    assert resp.status_code == 409


async def test_accept_respects_max_uses(client, login_user):
    ctx = await setup_company(client, login_user, "+79051250030")
    code = (await create_invite(client, ctx["owner"]["headers"], ctx["company_uuid"], max_uses=1)).json()["code"]

    first = await login_user("+79051250031")
    second = await login_user("+79051250032")
    assert (await client.post(f"/api/v1/invites/{code}/accept", headers=first["headers"])).status_code == 201
    assert (await client.post(f"/api/v1/invites/{code}/accept", headers=second["headers"])).status_code == 410


async def test_revoked_invite_is_gone(client, login_user):
    ctx = await setup_company(client, login_user, "+79051250040")
    invite = (await create_invite(client, ctx["owner"]["headers"], ctx["company_uuid"])).json()

    resp = await client.post(
        f"/api/v1/invites/{invite['invite_link_uuid']}/revoke", headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["active"] is False

    joiner = await login_user("+79051250041")
    resp = await client.post(f"/api/v1/invites/{invite['code']}/accept", headers=joiner["headers"])
    assert resp.status_code == 410


async def test_expired_invite_is_gone(client, login_user, expire_invite):
    ctx = await setup_company(client, login_user, "+79051250050")
    invite = (await create_invite(client, ctx["owner"]["headers"], ctx["company_uuid"], expires_in="24h")).json()
    await expire_invite(invite["invite_link_uuid"])

    joiner = await login_user("+79051250051")
    resp = await client.post(f"/api/v1/invites/{invite['code']}/accept", headers=joiner["headers"])
    assert resp.status_code == 410


async def test_invite_list_requires_invite_permission(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, "+79051250060")
    plain = await login_user("+79051250061")
    await add_team_member(ctx["company_uuid"], plain["me"]["user_uuid"], role="staff")

    resp = await client.get(f"/api/v1/companies/{ctx['company_uuid']}/invites", headers=plain["headers"])
    assert resp.status_code == 403
