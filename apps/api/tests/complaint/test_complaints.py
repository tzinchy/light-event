"""Жалобы (PLAN §3.7): подача участником, очередь и резолюция админом."""

from tests.balance.test_payout import apply_to_vacancy, setup_active_vacancy


async def post_complaint(client, headers, **overrides):
    payload = {
        "target_type": "company",
        "target_uuid": None,  # подставляется в тесте
        "kind": "Задержка оплаты",
        "severity": "high",
        "text": "Выплата за смену не пришла в срок",
        "vacancy_uuid": None,
    }
    payload.update(overrides)
    return await client.post("/api/v1/complaints", json=payload, headers=headers)


async def test_worker_files_complaint_and_sees_it(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790577700")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79057770013")

    resp = await post_complaint(
        client,
        worker["headers"],
        target_uuid=ctx["company_uuid"],
        vacancy_uuid=ctx["vacancy_uuid"],
    )
    assert resp.status_code == 201, resp.text
    complaint = resp.json()
    assert complaint["status"] == "open"
    assert complaint["kind"] == "Задержка оплаты"

    my = await client.get("/api/v1/complaints/my", headers=worker["headers"])
    assert my.status_code == 200
    assert [c["complaint_uuid"] for c in my.json()] == [complaint["complaint_uuid"]]


async def test_admin_resolves_complaint(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790577710")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79057771013")
    complaint = (
        await post_complaint(client, worker["headers"], target_uuid=ctx["company_uuid"])
    ).json()

    resp = await client.get("/api/v1/admin/complaints", headers=ctx["admin"]["headers"])
    assert resp.status_code == 200, resp.text
    assert complaint["complaint_uuid"] in {c["complaint_uuid"] for c in resp.json()}

    resp = await client.post(
        f"/api/v1/admin/complaints/{complaint['complaint_uuid']}/resolve",
        json={"action": "resolved", "resolution": "Организация провела выплату"},
        headers=ctx["admin"]["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "resolved"

    # закрытая жалоба уходит из открытой очереди
    open_uuids = {
        c["complaint_uuid"]
        for c in (await client.get("/api/v1/admin/complaints", headers=ctx["admin"]["headers"])).json()
    }
    assert complaint["complaint_uuid"] not in open_uuids

    # автор видит резолюцию
    my = (await client.get("/api/v1/complaints/my", headers=worker["headers"])).json()
    assert my[0]["status"] == "resolved"
    assert my[0]["resolution"] == "Организация провела выплату"


async def test_complaint_rbac_and_validation(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790577720")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79057772013")

    # без токена
    assert (await post_complaint(client, None, target_uuid=ctx["company_uuid"])).status_code == 401
    # неверная severity
    assert (
        await post_complaint(
            client, worker["headers"], target_uuid=ctx["company_uuid"], severity="urgent"
        )
    ).status_code == 422

    # admin-эндпоинты закрыты для обычного пользователя
    assert (await client.get("/api/v1/admin/complaints", headers=worker["headers"])).status_code == 403
    missing = "019f0000-0000-7000-8000-000000000000"
    resp = await client.post(
        f"/api/v1/admin/complaints/{missing}/resolve",
        json={"action": "dismissed", "resolution": "нет состава"},
        headers=ctx["admin"]["headers"],
    )
    assert resp.status_code == 404
