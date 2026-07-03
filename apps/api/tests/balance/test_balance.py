from tests.helpers import create_verified_company

from sqlalchemy import text


async def setup_company(client, login_user, base_phone: str) -> dict:
    owner = await login_user(base_phone + "1")
    company = await create_verified_company(client, owner["headers"])
    return {"owner": owner, "company_uuid": company["company_uuid"]}


async def upload_proof(client, headers) -> str:
    resp = await client.post(
        "/api/v1/documents",
        data={"kind": "payment_proof"},
        files={"file": ("proof.jpg", b"payment-proof-bytes", "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["document_uuid"]


async def create_topup(client, headers, company_uuid, amount_kop=500_000) -> dict:
    proof = await upload_proof(client, headers)
    resp = await client.post(
        f"/api/v1/companies/{company_uuid}/topup-requests",
        json={"amount_kop": amount_kop, "proof_document_uuid": proof, "payment_details": "Перевод по счёту №42"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login_admin(client, login_user, make_admin, phone: str) -> dict:
    admin = await login_user(phone)
    await make_admin(admin["me"]["user_uuid"])
    return admin


async def test_new_company_account_is_empty(client, login_user):
    ctx = await setup_company(client, login_user, "+7905126000")

    resp = await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"])

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["available_kop"] == 0
    assert body["on_hold_kop"] == 0
    assert body["total_kop"] == 0

    ops = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/account/operations", headers=ctx["owner"]["headers"]
    )
    assert ops.status_code == 200
    assert ops.json() == []


async def test_balance_requires_finance_permission(client, login_user, add_team_member):
    ctx = await setup_company(client, login_user, "+7905126010")
    staff = await login_user("+79051260102")
    outsider = await login_user("+79051260103")
    await add_team_member(ctx["company_uuid"], staff["me"]["user_uuid"], role="staff")

    for headers in (staff["headers"], outsider["headers"]):
        assert (
            await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=headers)
        ).status_code == 403
        assert (
            await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account/operations", headers=headers)
        ).status_code == 403
        proof = await upload_proof(client, headers)
        resp = await client.post(
            f"/api/v1/companies/{ctx['company_uuid']}/topup-requests",
            json={"amount_kop": 100_000, "proof_document_uuid": proof},
            headers=headers,
        )
        assert resp.status_code == 403


async def test_topup_request_is_created_pending(client, login_user):
    ctx = await setup_company(client, login_user, "+7905126020")

    topup = await create_topup(client, ctx["owner"]["headers"], ctx["company_uuid"])

    assert topup["status"] == "pending"
    assert topup["amount_kop"] == 500_000
    # заявка сама по себе ничего не зачисляет
    account = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"])
    ).json()
    assert account["available_kop"] == 0


async def test_admin_approves_topup_and_credits_account(client, login_user, make_admin, settings):
    ctx = await setup_company(client, login_user, "+7905126030")
    admin = await login_admin(client, login_user, make_admin, "+79051260302")
    topup = await create_topup(client, ctx["owner"]["headers"], ctx["company_uuid"], amount_kop=500_000)

    queue = (await client.get("/api/v1/admin/topup-requests", headers=admin["headers"])).json()
    assert topup["topup_request_uuid"] in [t["topup_request_uuid"] for t in queue]

    resp = await client.post(
        f"/api/v1/admin/topup-requests/{topup['topup_request_uuid']}/resolve",
        json={"action": "approve"},
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"

    account = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"])
    ).json()
    assert account["available_kop"] == 500_000
    assert account["total_kop"] == 500_000

    ops = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account/operations", headers=ctx["owner"]["headers"])
    ).json()
    assert len(ops) == 1
    assert ops[0]["kind"] == "topup"
    assert ops[0]["amount_kop"] == 500_000
    assert ops[0]["direction"] == "in"

    # сверка денормализованного баланса с журналом (skill money-ledger)
    from app.core.db import create_engine

    engine = create_engine(settings.database_url)
    async with engine.connect() as conn:
        recomputed = (
            await conn.execute(
                text(
                    """
                    SELECT COALESCE(SUM(CASE WHEN credit_account_uuid = a.account_uuid THEN amount_kop
                                             WHEN debit_account_uuid = a.account_uuid THEN -amount_kop END), 0)
                    FROM account a LEFT JOIN ledger_entry
                      ON a.account_uuid IN (credit_account_uuid, debit_account_uuid)
                    WHERE a.account_uuid = :u
                    GROUP BY a.account_uuid
                    """
                ),
                {"u": account["account_uuid"]},
            )
        ).scalar_one()
    await engine.dispose()
    assert recomputed == account["available_kop"] + account["on_hold_kop"]


async def test_admin_rejects_topup_without_credit(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+7905126040")
    admin = await login_admin(client, login_user, make_admin, "+79051260402")
    topup = await create_topup(client, ctx["owner"]["headers"], ctx["company_uuid"])

    resp = await client.post(
        f"/api/v1/admin/topup-requests/{topup['topup_request_uuid']}/resolve",
        json={"action": "reject", "reason": "Платёж не найден"},
        headers=admin["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "rejected"

    account = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"])
    ).json()
    assert account["available_kop"] == 0


async def test_topup_resolved_only_once(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+7905126050")
    admin = await login_admin(client, login_user, make_admin, "+79051260502")
    topup = await create_topup(client, ctx["owner"]["headers"], ctx["company_uuid"])

    url = f"/api/v1/admin/topup-requests/{topup['topup_request_uuid']}/resolve"
    assert (await client.post(url, json={"action": "approve"}, headers=admin["headers"])).status_code == 200
    assert (await client.post(url, json={"action": "approve"}, headers=admin["headers"])).status_code == 409

    # повторный resolve не удвоил баланс
    account = (
        await client.get(f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"])
    ).json()
    assert account["available_kop"] == 500_000


async def test_admin_endpoints_require_admin(client, login_user):
    ctx = await setup_company(client, login_user, "+7905126060")
    topup = await create_topup(client, ctx["owner"]["headers"], ctx["company_uuid"])

    resp = await client.get("/api/v1/admin/topup-requests", headers=ctx["owner"]["headers"])
    assert resp.status_code == 403

    resp = await client.post(
        f"/api/v1/admin/topup-requests/{topup['topup_request_uuid']}/resolve",
        json={"action": "approve"},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 403


async def test_topup_amount_must_be_positive(client, login_user):
    ctx = await setup_company(client, login_user, "+7905126070")
    proof = await upload_proof(client, ctx["owner"]["headers"])

    for bad_amount in (0, -100):
        resp = await client.post(
            f"/api/v1/companies/{ctx['company_uuid']}/topup-requests",
            json={"amount_kop": bad_amount, "proof_document_uuid": proof},
            headers=ctx["owner"]["headers"],
        )
        assert resp.status_code == 422


async def test_topup_proof_must_belong_to_requester(client, login_user):
    ctx = await setup_company(client, login_user, "+7905126080")
    stranger = await login_user("+79051260802")
    foreign_proof = await upload_proof(client, stranger["headers"])

    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/topup-requests",
        json={"amount_kop": 100_000, "proof_document_uuid": foreign_proof},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 404
