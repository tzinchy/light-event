"""Платёжные счета платформы: приоритет, лимиты, авто-подбор при пополнении (PLAN §11.9)."""

from tests.vacancy.test_vacancy import setup_company


async def _admin(login_user, make_admin, phone: str) -> dict:
    admin = await login_user(phone)
    await make_admin(admin["me"]["user_uuid"])
    return admin


async def _create_account(client, admin, name, limit_kop, priority=False) -> dict:
    resp = await client.post(
        "/api/v1/admin/payment-accounts",
        json={"name": name, "requisites": f"Реквизиты {name}", "monthly_limit_kop": limit_kop, "is_priority": priority},
        headers=admin["headers"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _topup(client, headers, company_uuid, amount_kop) -> dict:
    doc = await client.post(
        "/api/v1/documents",
        data={"kind": "payment_proof"},
        files={"file": ("proof.jpg", b"proof", "image/jpeg")},
        headers=headers,
    )
    resp = await client.post(
        f"/api/v1/companies/{company_uuid}/topup-requests",
        json={"amount_kop": amount_kop, "proof_document_uuid": doc.json()["document_uuid"]},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_only_admin_manages_accounts(client, login_user):
    user = await login_user("+79059000001")
    assert (await client.get("/api/v1/admin/payment-accounts", headers=user["headers"])).status_code == 403
    assert (await client.get("/api/v1/admin/payment-accounts")).status_code == 401


async def test_priority_account_selected_then_fallback_then_notify(client, login_user, make_admin):
    admin = await _admin(login_user, make_admin, "+79059001002")
    ctx = await setup_company(client, login_user, "+79059001003")
    company_uuid = ctx["company_uuid"]

    priority = await _create_account(client, admin, "Карта А", 100_000, priority=True)
    backup = await _create_account(client, admin, "Карта Б", 100_000)

    # влезает в приоритетный → выбран он, реквизиты в ответе
    t1 = await _topup(client, ctx["owner"]["headers"], company_uuid, 80_000)
    assert t1["payment_account_uuid"] == priority["payment_account_uuid"]
    assert t1["payment_requisites"] == "Реквизиты Карта А"

    # не влезает в остаток приоритетного (20 000 < 90 000) → берём запасной
    t2 = await _topup(client, ctx["owner"]["headers"], company_uuid, 90_000)
    assert t2["payment_account_uuid"] == backup["payment_account_uuid"]

    # свободного счёта под 90 000 не осталось → без счёта + уведомление админу
    t3 = await _topup(client, ctx["owner"]["headers"], company_uuid, 90_000)
    assert t3["payment_account_uuid"] is None
    notifs = (await client.get("/api/v1/notifications", headers=admin["headers"])).json()
    assert notifs["unread"] >= 1
    assert any(n["kind"] == "topup_no_account" for n in notifs["items"])


async def test_usage_shown_and_priority_switch(client, login_user, make_admin):
    admin = await _admin(login_user, make_admin, "+79059002002")
    ctx = await setup_company(client, login_user, "+79059002003")

    a = await _create_account(client, admin, "Карта А", 500_000, priority=True)
    b = await _create_account(client, admin, "Карта Б", 500_000)
    await _topup(client, ctx["owner"]["headers"], ctx["company_uuid"], 120_000)

    listed = (await client.get("/api/v1/admin/payment-accounts", headers=admin["headers"])).json()
    by_id = {x["payment_account_uuid"]: x for x in listed}
    assert by_id[a["payment_account_uuid"]]["received_this_month_kop"] == 120_000

    # смена приоритета
    resp = await client.post(
        f"/api/v1/admin/payment-accounts/{b['payment_account_uuid']}/priority", headers=admin["headers"]
    )
    assert resp.status_code == 200
    listed = (await client.get("/api/v1/admin/payment-accounts", headers=admin["headers"])).json()
    by_id = {x["payment_account_uuid"]: x for x in listed}
    assert by_id[b["payment_account_uuid"]]["is_priority"] is True
    assert by_id[a["payment_account_uuid"]]["is_priority"] is False
