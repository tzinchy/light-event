"""Тарифы услуг редактирует админ; списания берут актуальную цену (PLAN §11.6-B)."""

from tests.test.test_tests import create_company_test, setup_company


async def _prices(client, headers) -> dict[str, int]:
    resp = await client.get("/api/v1/admin/pricing", headers=headers)
    assert resp.status_code == 200, resp.text
    return {row["key"]: row["amount_kop"] for row in resp.json()}


async def test_defaults_returned_when_no_overrides(client, login_user, make_admin):
    admin = await login_user("+79051400001")
    await make_admin(admin["me"]["user_uuid"])

    prices = await _prices(client, admin["headers"])
    assert prices["vacancy_publish"] == 99_000
    assert prices["company_test"] == 150_000


async def test_only_admin_can_read_and_edit(client, login_user, make_admin):
    user = await login_user("+79051400011")

    assert (await client.get("/api/v1/admin/pricing", headers=user["headers"])).status_code == 403
    resp = await client.put(
        "/api/v1/admin/pricing/company_test", json={"amount_kop": 50_000}, headers=user["headers"]
    )
    assert resp.status_code == 403


async def test_unknown_key_rejected(client, login_user, make_admin):
    admin = await login_user("+79051400021")
    await make_admin(admin["me"]["user_uuid"])

    resp = await client.put(
        "/api/v1/admin/pricing/teleport", json={"amount_kop": 100}, headers=admin["headers"]
    )
    assert resp.status_code == 404


async def test_updated_price_applies_to_test_fee(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905140010")  # фонд 300 000
    admin = ctx["admin"]

    resp = await client.put(
        "/api/v1/admin/pricing/company_test", json={"amount_kop": 50_000}, headers=admin["headers"]
    )
    assert resp.status_code == 200, resp.text
    assert (await _prices(client, admin["headers"]))["company_test"] == 50_000

    await create_company_test(client, ctx)  # должно списать новую цену 50 000, а не 150 000

    acc = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"]
    )
    assert acc.json()["available_kop"] == 300_000 - 50_000
