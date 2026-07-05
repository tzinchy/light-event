"""Публичный профиль компании: активные события фильтруются по company_uuid (PLAN §11.7-B)."""

from tests.balance.test_payout import setup_active_vacancy


async def test_feed_filtered_by_company(client, login_user, make_admin):
    ctx = await setup_active_vacancy(client, login_user, make_admin, "+790581100")
    company_uuid = ctx["company_uuid"]

    mine = (await client.get(f"/api/v1/vacancies?company_uuid={company_uuid}")).json()
    assert len(mine) == 1
    assert mine[0]["company_uuid"] == company_uuid

    other = "019f2f4e-0000-7000-8000-000000000000"
    assert (await client.get(f"/api/v1/vacancies?company_uuid={other}")).json() == []
