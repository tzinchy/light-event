"""Отзывы (PLAN §3.7): после выплаты, один на пару (автор, заявка), рейтинги — агрегаты."""

from tests.balance.test_payout import (
    apply_to_vacancy,
    confirm,
    setup_active_vacancy,
)


async def paid_application(client, login_user, make_admin, base_phone: str) -> tuple[dict, dict]:
    """Полный цикл до выплаты: заявка соискателя в статусе paid."""
    ctx = await setup_active_vacancy(client, login_user, make_admin, base_phone)
    worker = await apply_to_vacancy(client, login_user, ctx, base_phone + "13")
    assert (await confirm(client, ctx, worker["application_uuid"])).status_code == 200
    resp = await client.get("/api/v1/admin/payouts", headers=ctx["admin"]["headers"])
    payout = next(p for p in resp.json() if p["vacancy_uuid"] == ctx["vacancy_uuid"])
    resp = await client.post(
        f"/api/v1/admin/payouts/{payout['payout_uuid']}/execute", headers=ctx["admin"]["headers"]
    )
    assert resp.status_code == 200, resp.text
    return ctx, worker


async def post_review(client, headers, application_uuid: str, **overrides):
    payload = {
        "application_uuid": application_uuid,
        "rating": 5,
        "text": "Отличная организация, выплата вовремя",
        "kind": "about_org",
    }
    payload.update(overrides)
    return await client.post("/api/v1/reviews", json=payload, headers=headers)


async def test_worker_reviews_company_after_payout(client, login_user, make_admin):
    ctx, worker = await paid_application(client, login_user, make_admin, "+790566600")

    resp = await post_review(client, worker["headers"], worker["application_uuid"])
    assert resp.status_code == 201, resp.text

    resp = await client.get(f"/api/v1/companies/{ctx['company_uuid']}/reviews")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["count"] == 1
    assert data["avg_rating"] == 5.0
    assert data["items"][0]["text"] == "Отличная организация, выплата вовремя"
    assert data["items"][0]["kind"] == "about_org"


async def test_second_review_for_same_application_conflicts(client, login_user, make_admin):
    _, worker = await paid_application(client, login_user, make_admin, "+790566610")

    assert (await post_review(client, worker["headers"], worker["application_uuid"])).status_code == 201
    resp = await post_review(
        client, worker["headers"], worker["application_uuid"], rating=1, kind="about_event"
    )
    assert resp.status_code == 409


async def test_review_before_payout_is_rejected(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790566620")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79056662013")
    assert (await confirm(client, ctx, worker["application_uuid"])).status_code == 200

    resp = await post_review(client, worker["headers"], worker["application_uuid"])
    assert resp.status_code == 409


async def test_outsider_cannot_review_foreign_application(client, login_user, make_admin):
    _, worker = await paid_application(client, login_user, make_admin, "+790566630")
    outsider = await login_user("+79056663019")

    resp = await post_review(client, outsider["headers"], worker["application_uuid"])
    assert resp.status_code == 403


async def test_manager_reviews_worker(client, login_user, make_admin):
    ctx, worker = await paid_application(client, login_user, make_admin, "+790566640")

    resp = await post_review(
        client,
        ctx["owner"]["headers"],
        worker["application_uuid"],
        kind="about_worker",
        rating=4,
        text="Пунктуальный, аккуратный",
    )
    assert resp.status_code == 201, resp.text

    resp = await client.get(f"/api/v1/users/{worker['me']['user_uuid']}/reviews")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["count"] == 1
    assert data["avg_rating"] == 4.0
    assert data["items"][0]["kind"] == "about_worker"


async def test_rating_bounds_validated(client, login_user, make_admin):
    _, worker = await paid_application(client, login_user, make_admin, "+790566650")

    assert (await post_review(client, worker["headers"], worker["application_uuid"], rating=0)).status_code == 422
    assert (await post_review(client, worker["headers"], worker["application_uuid"], rating=6)).status_code == 422
