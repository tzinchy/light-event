async def create_company(client, headers, name="Гранд Холл «Метрополь»") -> dict:
    resp = await client.post("/api/v1/companies", json={"name": name}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_company_makes_creator_main_manager(client, login_user):
    session = await login_user()

    company = await create_company(client, session["headers"])
    assert company["status"] == "pending"
    assert company["name"] == "Гранд Холл «Метрополь»"

    resp = await client.get(f"/api/v1/companies/{company['company_uuid']}/team", headers=session["headers"])
    assert resp.status_code == 200
    team = resp.json()
    assert len(team) == 1
    member = team[0]
    assert member["user_uuid"] == session["me"]["user_uuid"]
    assert member["company_role"] == "main_manager"
    assert member["perm_create"] and member["perm_hire"] and member["perm_finance"] and member["perm_invite"]


async def test_company_is_publicly_readable(client, login_user):
    owner = await login_user("+79051230010")
    company = await create_company(client, owner["headers"])

    resp = await client.get(f"/api/v1/companies/{company['company_uuid']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == company["name"]


async def test_patch_company_requires_main_manager(client, login_user, add_team_member):
    owner = await login_user("+79051230011")
    manager = await login_user("+79051230012")
    stranger = await login_user("+79051230013")
    company = await create_company(client, owner["headers"])
    url = f"/api/v1/companies/{company['company_uuid']}"
    await add_team_member(company["company_uuid"], manager["me"]["user_uuid"], role="manager")

    resp = await client.patch(url, json={"description": "Хакнуто"}, headers=stranger["headers"])
    assert resp.status_code == 403

    # даже менеджер с правами не редактирует компанию — только main_manager
    resp = await client.patch(url, json={"description": "Хакнуто"}, headers=manager["headers"])
    assert resp.status_code == 403

    resp = await client.patch(url, json={"description": "Банкетный зал"}, headers=owner["headers"])
    assert resp.status_code == 200
    assert resp.json()["description"] == "Банкетный зал"


async def test_team_list_requires_membership(client, login_user):
    owner = await login_user("+79051230014")
    stranger = await login_user("+79051230015")
    company = await create_company(client, owner["headers"])

    resp = await client.get(f"/api/v1/companies/{company['company_uuid']}/team", headers=stranger["headers"])
    assert resp.status_code == 403

    resp = await client.get(f"/api/v1/companies/{company['company_uuid']}/team")
    assert resp.status_code == 401


async def test_my_companies_lists_only_memberships(client, login_user):
    owner = await login_user("+79051230060")
    outsider = await login_user("+79051230061")
    company = await create_company(client, owner["headers"])

    resp = await client.get("/api/v1/companies/my", headers=owner["headers"])
    assert resp.status_code == 200, resp.text
    mine = resp.json()
    assert [c["company"]["company_uuid"] for c in mine] == [company["company_uuid"]]
    assert mine[0]["company_role"] == "main_manager"

    resp = await client.get("/api/v1/companies/my", headers=outsider["headers"])
    assert resp.status_code == 200
    assert resp.json() == []
