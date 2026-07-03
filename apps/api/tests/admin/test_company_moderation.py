"""Админская модерация заявок организаций: список pending, подтверждение, отклонение."""

from tests.company.test_company_application import VALID_APPLICATION


async def submit_application(client, headers) -> str:
    resp = await client.post("/api/v1/companies", json=VALID_APPLICATION, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["company_uuid"]


async def test_moderation_endpoints_require_admin(client, login_user):
    user = await login_user("+79053330001")

    assert (await client.get("/api/v1/admin/companies")).status_code == 401
    assert (await client.get("/api/v1/admin/companies", headers=user["headers"])).status_code == 403
    missing = "019f0000-0000-7000-8000-000000000000"
    assert (
        await client.post(f"/api/v1/admin/companies/{missing}/verify", headers=user["headers"])
    ).status_code == 403


async def test_admin_sees_pending_applications_with_requisites(client, login_user, make_admin):
    owner = await login_user("+79053330002")
    admin = await login_user("+79053330003")
    await make_admin(admin["me"]["user_uuid"])
    company_uuid = await submit_application(client, owner["headers"])

    resp = await client.get("/api/v1/admin/companies?status=pending", headers=admin["headers"])

    assert resp.status_code == 200, resp.text
    apps = {c["company_uuid"]: c for c in resp.json()}
    assert company_uuid in apps
    assert apps[company_uuid]["inn"] == VALID_APPLICATION["inn"]
    assert apps[company_uuid]["ogrn"] == VALID_APPLICATION["ogrn"]
    assert apps[company_uuid]["contact_phone"] == VALID_APPLICATION["contact_phone"]


async def test_verify_opens_company_cabinet(client, login_user, make_admin):
    owner = await login_user("+79053330004")
    admin = await login_user("+79053330005")
    await make_admin(admin["me"]["user_uuid"])
    company_uuid = await submit_application(client, owner["headers"])

    resp = await client.post(f"/api/v1/admin/companies/{company_uuid}/verify", headers=admin["headers"])

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "verified"
    assert resp.json()["verified_at"] is not None

    # кабинет открылся
    filial = await client.post(
        f"/api/v1/companies/{company_uuid}/filials",
        json={"name": "Филиал", "address": "Адрес, 1"},
        headers=owner["headers"],
    )
    assert filial.status_code == 201, filial.text


async def test_reject_with_reason_visible_to_owner(client, login_user, make_admin):
    owner = await login_user("+79053330006")
    admin = await login_user("+79053330007")
    await make_admin(admin["me"]["user_uuid"])
    company_uuid = await submit_application(client, owner["headers"])

    resp = await client.post(
        f"/api/v1/admin/companies/{company_uuid}/reject",
        json={"reason": "Реквизиты не совпадают с ЕГРЮЛ"},
        headers=admin["headers"],
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "rejected"

    my = await client.get("/api/v1/companies/my", headers=owner["headers"])
    company = my.json()[0]["company"]
    assert company["status"] == "rejected"
    assert company["reject_reason"] == "Реквизиты не совпадают с ЕГРЮЛ"

    # кабинет по-прежнему закрыт
    assert (
        await client.get(f"/api/v1/companies/{company_uuid}/team", headers=owner["headers"])
    ).status_code == 403


async def test_verify_missing_company_returns_404(client, login_user, make_admin):
    admin = await login_user("+79053330008")
    await make_admin(admin["me"]["user_uuid"])
    missing = "019f0000-0000-7000-8000-000000000000"

    assert (
        await client.post(f"/api/v1/admin/companies/{missing}/verify", headers=admin["headers"])
    ).status_code == 404
