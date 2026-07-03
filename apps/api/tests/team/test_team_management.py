from tests.helpers import create_verified_company

async def setup_company(client, login_user, add_team_member, base_phone: str) -> dict:
    owner = await login_user(base_phone + "1")
    manager = await login_user(base_phone + "2")
    company_uuid = (await create_verified_company(client, owner["headers"]))["company_uuid"]
    await add_team_member(company_uuid, manager["me"]["user_uuid"], role="manager", perm_create=True)

    team = (await client.get(f"/api/v1/companies/{company_uuid}/team", headers=owner["headers"])).json()
    by_role = {m["company_role"]: m for m in team}
    return {"owner": owner, "manager": manager, "company_uuid": company_uuid, "team": by_role}


async def test_main_manager_toggles_member_permissions(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, add_team_member, "+7905124000")
    member_uuid = ctx["team"]["manager"]["team_member_uuid"]

    resp = await client.patch(
        f"/api/v1/team-members/{member_uuid}/permissions",
        json={"perm_hire": True, "perm_create": False},
        headers=ctx["owner"]["headers"],
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["perm_hire"] is True
    assert body["perm_create"] is False
    assert body["perm_finance"] is False


async def test_manager_cannot_change_permissions(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, add_team_member, "+7905124010")
    member_uuid = ctx["team"]["manager"]["team_member_uuid"]

    resp = await client.patch(
        f"/api/v1/team-members/{member_uuid}/permissions",
        json={"perm_finance": True},
        headers=ctx["manager"]["headers"],
    )

    assert resp.status_code == 403


async def test_main_manager_permissions_are_locked(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, add_team_member, "+7905124020")
    owner_member_uuid = ctx["team"]["main_manager"]["team_member_uuid"]

    resp = await client.patch(
        f"/api/v1/team-members/{owner_member_uuid}/permissions",
        json={"perm_finance": False},
        headers=ctx["owner"]["headers"],
    )

    assert resp.status_code == 403


async def test_main_manager_removes_member_but_not_himself(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, add_team_member, "+7905124030")
    manager_uuid = ctx["team"]["manager"]["team_member_uuid"]
    owner_uuid = ctx["team"]["main_manager"]["team_member_uuid"]

    resp = await client.delete(f"/api/v1/team-members/{owner_uuid}", headers=ctx["owner"]["headers"])
    assert resp.status_code == 403

    resp = await client.delete(f"/api/v1/team-members/{manager_uuid}", headers=ctx["owner"]["headers"])
    assert resp.status_code == 204

    team = (await client.get(f"/api/v1/companies/{ctx['company_uuid']}/team", headers=ctx["owner"]["headers"])).json()
    assert [m["company_role"] for m in team] == ["main_manager"]


async def test_member_cannot_remove_others(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, add_team_member, "+7905124040")
    owner_member_uuid = ctx["team"]["main_manager"]["team_member_uuid"]

    resp = await client.delete(f"/api/v1/team-members/{owner_member_uuid}", headers=ctx["manager"]["headers"])
    assert resp.status_code == 403
