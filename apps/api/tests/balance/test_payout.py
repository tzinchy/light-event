"""Payout-цикл (PLAN §11.4): резерв on_hold при подтверждении, выплата админом, комиссия 6%.

Комиссия удерживается из суммы выплаты: соискатель получает 94% итога за смену.
"""

from sqlalchemy import text

from app.core.db import create_engine
from tests import helpers
from tests.vacancy.test_vacancy import create_draft, fund_company, moderate, publish, setup_company

PAY_TOTAL_KOP = 315_000  # 7 ч × 450 ₽/час (vacancy_payload)
COMMISSION_KOP = PAY_TOTAL_KOP * 6 // 100  # 18 900
WORKER_SHARE_KOP = PAY_TOTAL_KOP - COMMISSION_KOP  # 296 100


async def setup_active_vacancy(client, login_user, make_admin, base_phone: str) -> dict:
    ctx = await setup_company(client, login_user, base_phone + "1")
    # 990 ₽ публикация + резерв под двух подтверждённых (2 × 3 150 ₽)
    await fund_company(client, login_user, make_admin, ctx, base_phone + "2", amount_kop=1_000_000)
    vacancy = await create_draft(client, ctx)
    assert (await publish(client, ctx, vacancy["vacancy_uuid"])).status_code == 200
    assert (await moderate(client, ctx, vacancy["vacancy_uuid"], "approve")).status_code == 200
    ctx["vacancy_uuid"] = vacancy["vacancy_uuid"]
    return ctx


async def apply_to_vacancy(client, login_user, ctx, phone: str) -> dict:
    worker = await login_user(phone)
    resp = await client.post(
        f"/api/v1/vacancies/{ctx['vacancy_uuid']}/applications", headers=worker["headers"]
    )
    assert resp.status_code == 201, resp.text
    worker["application_uuid"] = resp.json()["application_uuid"]
    return worker


async def confirm(client, ctx, application_uuid: str):
    return await client.post(
        f"/api/v1/applications/{application_uuid}/status",
        json={"action": "confirm"},
        headers=ctx["owner"]["headers"],
    )


async def company_account(client, ctx) -> dict:
    resp = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/account", headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def account_row(owner_type: str, owner_uuid: str) -> tuple[int, int] | None:
    """Прямое чтение счёта из БД — у соискателя/платформы нет API-баланса."""
    assert helpers.DB_URL is not None
    engine = create_engine(helpers.DB_URL)
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT available_kop, on_hold_kop FROM account WHERE owner_type = :t AND owner_uuid = :o"),
                {"t": owner_type, "o": owner_uuid},
            )
        ).first()
    await engine.dispose()
    return None if row is None else (row[0], row[1])


async def test_confirm_holds_pay_total_and_creates_payout(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790555500")
    before = await company_account(client, ctx)

    worker = await apply_to_vacancy(client, login_user, ctx, "+79055550013")
    assert (await confirm(client, ctx, worker["application_uuid"])).status_code == 200

    acc = await company_account(client, ctx)
    assert acc["available_kop"] == before["available_kop"] - PAY_TOTAL_KOP
    assert acc["on_hold_kop"] == before["on_hold_kop"] + PAY_TOTAL_KOP

    resp = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/payouts", headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 200, resp.text
    payouts = resp.json()
    assert len(payouts) == 1
    assert payouts[0]["status"] == "pending"
    assert payouts[0]["amount_kop"] == PAY_TOTAL_KOP
    assert payouts[0]["workers_count"] == 1

    # второй подтверждённый — резерв и заявка на выплату растут
    worker2 = await apply_to_vacancy(client, login_user, ctx, "+79055550014")
    assert (await confirm(client, ctx, worker2["application_uuid"])).status_code == 200
    payouts = (
        await client.get(
            f"/api/v1/companies/{ctx['company_uuid']}/payouts", headers=ctx["owner"]["headers"]
        )
    ).json()
    assert len(payouts) == 1
    assert payouts[0]["amount_kop"] == 2 * PAY_TOTAL_KOP
    assert payouts[0]["workers_count"] == 2


async def test_confirm_without_funds_is_rejected(client, login_user, make_admin):
    # хватает ровно на публикацию (990 ₽), на резерв под выплату — нет
    ctx = await setup_company(client, login_user, "+79055551001")
    await fund_company(client, login_user, make_admin, ctx, "+79055551002", amount_kop=99_000)
    vacancy = await create_draft(client, ctx)
    assert (await publish(client, ctx, vacancy["vacancy_uuid"])).status_code == 200
    assert (await moderate(client, ctx, vacancy["vacancy_uuid"], "approve")).status_code == 200
    ctx["vacancy_uuid"] = vacancy["vacancy_uuid"]

    worker = await apply_to_vacancy(client, login_user, ctx, "+79055551003")
    resp = await confirm(client, ctx, worker["application_uuid"])

    assert resp.status_code == 409
    acc = await company_account(client, ctx)
    assert acc["available_kop"] == 0
    assert acc["on_hold_kop"] == 0
    # заявка осталась на рассмотрении — подтверждение откатилось целиком
    detail = await client.get(
        f"/api/v1/applications/{worker['application_uuid']}", headers=worker["headers"]
    )
    assert detail.json()["status"] == "review"


async def test_execute_payout_pays_workers_and_commission(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790555520")
    worker = await apply_to_vacancy(client, login_user, ctx, "+79055552013")
    assert (await confirm(client, ctx, worker["application_uuid"])).status_code == 200

    resp = await client.get("/api/v1/admin/payouts", headers=ctx["admin"]["headers"])
    assert resp.status_code == 200, resp.text
    payout = next(p for p in resp.json() if p["vacancy_uuid"] == ctx["vacancy_uuid"])

    platform_before = await account_row("platform", "00000000-0000-0000-0000-000000000000")

    resp = await client.post(
        f"/api/v1/admin/payouts/{payout['payout_uuid']}/execute", headers=ctx["admin"]["headers"]
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "paid"

    # резерв списан целиком
    acc = await company_account(client, ctx)
    assert acc["on_hold_kop"] == 0

    # соискатель получил 94%, платформа — 6%
    worker_acc = await account_row("user", worker["me"]["user_uuid"])
    assert worker_acc == (WORKER_SHARE_KOP, 0)
    platform_after = await account_row("platform", "00000000-0000-0000-0000-000000000000")
    platform_gain = platform_after[0] - (platform_before[0] if platform_before else 0)
    assert platform_gain == COMMISSION_KOP

    # заявка соискателя закрыта выплатой, в таймлайне — шаг payout
    detail = (
        await client.get(
            f"/api/v1/applications/{worker['application_uuid']}", headers=worker["headers"]
        )
    ).json()
    assert detail["status"] == "paid"
    assert "payout" in {e["kind"] for e in detail["timeline"]}

    # повторное проведение невозможно
    resp = await client.post(
        f"/api/v1/admin/payouts/{payout['payout_uuid']}/execute", headers=ctx["admin"]["headers"]
    )
    assert resp.status_code == 409


async def test_payout_endpoints_require_roles(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790555530")
    outsider = await login_user("+79055553013")

    # список выплат компании — только команда с perm_finance
    resp = await client.get(
        f"/api/v1/companies/{ctx['company_uuid']}/payouts", headers=outsider["headers"]
    )
    assert resp.status_code == 403

    # админские выплаты — не для обычного пользователя
    assert (await client.get("/api/v1/admin/payouts")).status_code == 401
    assert (await client.get("/api/v1/admin/payouts", headers=outsider["headers"])).status_code == 403
    missing = "019f0000-0000-7000-8000-000000000000"
    assert (
        await client.post(f"/api/v1/admin/payouts/{missing}/execute", headers=outsider["headers"])
    ).status_code == 403
    assert (
        await client.post(f"/api/v1/admin/payouts/{missing}/execute", headers=ctx["admin"]["headers"])
    ).status_code == 404
