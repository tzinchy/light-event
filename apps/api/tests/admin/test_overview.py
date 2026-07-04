"""Admin overview (PLAN §5, §9.13): сводные метрики и счётчики очередей."""

from tests.balance.test_payout import apply_to_vacancy, confirm, setup_active_vacancy


async def test_overview_requires_admin(client, login_user):
    user = await login_user("+79058880001")

    assert (await client.get("/api/v1/admin/overview")).status_code == 401
    assert (await client.get("/api/v1/admin/overview", headers=user["headers"])).status_code == 403


async def test_overview_counts_users_turnover_and_queues(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790588810")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79058881013")
    assert (await confirm(client, ctx, worker["application_uuid"])).status_code == 200

    # открытая жалоба — попадает в «Споры»
    resp = await client.post(
        "/api/v1/complaints",
        json={
            "target_type": "company",
            "target_uuid": ctx["company_uuid"],
            "kind": "Задержка оплаты",
            "severity": "high",
            "text": "Тестовая жалоба",
        },
        headers=worker["headers"],
    )
    assert resp.status_code == 201

    resp = await client.get("/api/v1/admin/overview", headers=ctx["admin"]["headers"])
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # минимум трое: владелец, админ, соискатель
    assert data["users_count"] >= 3
    # оборот = зачисленные пополнения; setup пополнял на 1 000 000 коп
    assert data["turnover_kop"] >= 1_000_000
    # KYC-доля — число 0..100 (документы в этом сценарии не загружались)
    assert 0 <= data["kyc_verified_pct"] <= 100
    assert data["open_complaints"] >= 1

    queues = data["queues"]
    # у смены один подтверждённый → есть выплата к проведению
    assert queues["payouts"] >= 1
    assert queues["complaints"] >= 1
    # счётчики всех очередей присутствуют
    for key in ("companies", "requests", "topups", "payouts", "kyc", "complaints"):
        assert key in queues
