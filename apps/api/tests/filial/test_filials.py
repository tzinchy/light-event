async def make_company(client, headers) -> str:
    resp = await client.post("/api/v1/companies", json={"name": "Гранд Холл"}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["company_uuid"]


async def test_main_manager_manages_filials(client, login_user):
    owner = await login_user("+79051230020")
    company_uuid = await make_company(client, owner["headers"])
    base = f"/api/v1/companies/{company_uuid}/filials"

    resp = await client.post(
        base,
        json={"name": "Гранд Холл — Тверская", "address": "Тверская, 9", "lat": 55.7649, "lon": 37.6049},
        headers=owner["headers"],
    )
    assert resp.status_code == 201, resp.text
    filial = resp.json()
    assert filial["name"] == "Гранд Холл — Тверская"
    assert filial["lat"] == 55.7649

    resp = await client.get(base, headers=owner["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.patch(
        f"/api/v1/filials/{filial['filial_uuid']}", json={"name": "Гранд Холл — Арбат"}, headers=owner["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Гранд Холл — Арбат"

    resp = await client.delete(f"/api/v1/filials/{filial['filial_uuid']}", headers=owner["headers"])
    assert resp.status_code == 204

    resp = await client.get(base, headers=owner["headers"])
    assert resp.json() == []


async def test_filial_changes_denied_for_non_main_manager(client, login_user, add_team_member):
    owner = await login_user("+79051230021")
    manager = await login_user("+79051230022")
    stranger = await login_user("+79051230023")
    company_uuid = await make_company(client, owner["headers"])
    base = f"/api/v1/companies/{company_uuid}/filials"
    await add_team_member(company_uuid, manager["me"]["user_uuid"], role="manager", perm_create=True)

    payload = {"name": "Филиал", "address": "Адрес"}
    assert (await client.post(base, json=payload, headers=manager["headers"])).status_code == 403
    assert (await client.post(base, json=payload, headers=stranger["headers"])).status_code == 403

    # список филиалов доступен члену команды, но не постороннему
    assert (await client.get(base, headers=manager["headers"])).status_code == 200
    assert (await client.get(base, headers=stranger["headers"])).status_code == 403
