"""Единая очередь модерации админа: vacancy + test в pending_moderation (PLAN §11.1)."""

from tests.test.test_tests import QUESTIONS
from tests.vacancy.test_vacancy import create_draft, fund_company, publish, setup_company


async def test_requests_queue_requires_admin(client, login_user):
    user = await login_user("+79054440001")

    assert (await client.get("/api/v1/admin/requests")).status_code == 401
    assert (await client.get("/api/v1/admin/requests", headers=user["headers"])).status_code == 403


async def test_pending_items_in_queue_and_leave_after_moderation(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, "+79054440002")
    await fund_company(client, login_user, make_admin, ctx, "+79054440003")

    vacancy = await create_draft(client, ctx)
    assert (await publish(client, ctx, vacancy["vacancy_uuid"])).status_code == 200

    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/tests",
        json={"title": "Стандарты Гранд Холл", "topic": "Официант", "min_correct": 2, "questions": QUESTIONS},
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 201, resp.text
    test_uuid = resp.json()["test_uuid"]
    # черновик попадает в очередь модерации только после отправки (списывается тариф)
    submit = await client.post(f"/api/v1/tests/{test_uuid}/submit", headers=ctx["owner"]["headers"])
    assert submit.status_code == 200, submit.text

    resp = await client.get("/api/v1/admin/requests", headers=ctx["admin"]["headers"])
    assert resp.status_code == 200, resp.text
    items = {(i["kind"], i["ref_uuid"]): i for i in resp.json()}

    v = items[("vacancy", vacancy["vacancy_uuid"])]
    assert v["title"] == "Свадебный банкет"
    assert v["company_name"] == "Гранд Холл «Метрополь»"
    assert v["submitted_at"]

    t = items[("test", test_uuid)]
    assert t["title"] == "Стандарты Гранд Холл"

    # одобренная вакансия уходит из очереди, тест остаётся
    resp = await client.post(
        f"/api/v1/admin/vacancies/{vacancy['vacancy_uuid']}/moderate",
        json={"action": "approve", "reason": None},
        headers=ctx["admin"]["headers"],
    )
    assert resp.status_code == 200, resp.text

    resp = await client.get("/api/v1/admin/requests", headers=ctx["admin"]["headers"])
    keys = {(i["kind"], i["ref_uuid"]) for i in resp.json()}
    assert ("vacancy", vacancy["vacancy_uuid"]) not in keys
    assert ("test", test_uuid) in keys
