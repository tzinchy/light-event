"""Per-company тарифы + плата за сотрудника после смены (PLAN §11.10-A/B)."""

from tests.balance.test_payout import apply_to_vacancy, confirm, company_account, setup_active_vacancy
from tests.test.test_tests import setup_company, test_payload


async def _set_company_price(client, admin, company_uuid: str, key: str, amount_kop: int):
    resp = await client.put(
        f"/api/v1/admin/companies/{company_uuid}/pricing/{key}",
        json={"amount_kop": amount_kop},
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_company_override_applies_only_to_that_company(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+790591100")  # фонд 300 000
    company_uuid = ctx["company_uuid"]

    # тариф теста именно для этой компании — 50 000 вместо дефолтных 150 000
    await _set_company_price(client, ctx["admin"], company_uuid, "company_test", 50_000)

    # участник видит эффективную цену со своим override
    prices = (
        await client.get(f"/api/v1/companies/{company_uuid}/pricing", headers=ctx["owner"]["headers"])
    ).json()
    by_key = {p["key"]: p for p in prices}
    assert by_key["company_test"]["amount_kop"] == 50_000
    assert by_key["company_test"]["company_override"] is True
    assert by_key["vacancy_publish"]["company_override"] is False

    # черновик + отправка на модерацию списывает цену компании
    test = (
        await client.post(
            f"/api/v1/companies/{company_uuid}/tests", json=test_payload(), headers=ctx["owner"]["headers"]
        )
    ).json()
    assert (
        await client.post(f"/api/v1/tests/{test['test_uuid']}/submit", headers=ctx["owner"]["headers"])
    ).status_code == 200
    acc = await client.get(f"/api/v1/companies/{company_uuid}/account", headers=ctx["owner"]["headers"])
    assert acc.json()["available_kop"] == 300_000 - 50_000

    # чужой участник не видит цены этой компании
    outsider = await login_user("+79059110099")
    assert (
        await client.get(f"/api/v1/companies/{company_uuid}/pricing", headers=outsider["headers"])
    ).status_code == 403


async def test_worker_completion_fee_charged_on_payout(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790591200")
    # фикс-плата 20 000 коп за сотрудника — только для этой компании
    await _set_company_price(client, ctx["admin"], ctx["company_uuid"], "worker_completion", 20_000)

    worker = await apply_to_vacancy(client, login_user, ctx, "+79059120013")
    assert (await confirm(client, ctx, worker["application_uuid"])).status_code == 200
    before = await company_account(client, ctx)

    payouts = (await client.get("/api/v1/admin/payouts", headers=ctx["admin"]["headers"])).json()
    payout = next(p for p in payouts if p["vacancy_uuid"] == ctx["vacancy_uuid"])
    resp = await client.post(
        f"/api/v1/admin/payouts/{payout['payout_uuid']}/execute", headers=ctx["admin"]["headers"]
    )
    assert resp.status_code == 200, resp.text

    # с available списана фикс-плата за 1 сотрудника (резерв ушёл отдельно из on_hold)
    after = await company_account(client, ctx)
    assert after["available_kop"] == before["available_kop"] - 20_000
    ops = (
        await client.get(
            f"/api/v1/companies/{ctx['company_uuid']}/account/operations", headers=ctx["owner"]["headers"]
        )
    ).json()
    assert any(o["kind"] == "completion_fee" for o in ops)
