"""Условие заявки: откликнуться может только тот, кто прошёл обязательные тесты (PLAN §11.6-D)."""

from tests.test.test_tests import answer_all, create_company_test, setup_company, start_attempt


async def _filial(client, ctx) -> str:
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/filials",
        json={"name": "Тверская", "address": "Тверская, 9"},
        headers=ctx["owner"]["headers"],
    )
    return resp.json()["filial_uuid"]


async def _active_vacancy(client, ctx, filial_uuid: str, required: list[str] | None) -> tuple[str, dict]:
    payload = {
        "filial_uuid": filial_uuid,
        "role_name": "Официант",
        "event_title": "Свадебный банкет",
        "starts_at": "2026-07-12T16:00:00+03:00",
        "ends_at": "2026-07-12T23:00:00+03:00",
        "venue_address": "Тверская, 9",
        "pay_hour_kop": 45_000,
        "slots": 2,
    }
    if required is not None:
        payload["required_test_uuids"] = required
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies", json=payload, headers=ctx["owner"]["headers"]
    )
    assert resp.status_code == 201, resp.text
    out = resp.json()
    vacancy_uuid = out["vacancy_uuid"]
    await client.post(f"/api/v1/vacancies/{vacancy_uuid}/publish", headers=ctx["owner"]["headers"])
    await client.post(
        f"/api/v1/admin/vacancies/{vacancy_uuid}/moderate",
        json={"action": "approve"},
        headers=ctx["admin"]["headers"],
    )
    return vacancy_uuid, out


async def _pass_test(client, headers, test_uuid: str) -> None:
    attempt = (await start_attempt(client, headers, test_uuid)).json()
    await answer_all(client, headers, attempt, correct=True)
    resp = await client.post(f"/api/v1/attempts/{attempt['test_attempt_uuid']}/finish", headers=headers)
    assert resp.json()["passed"] is True


async def _apply(client, headers, vacancy_uuid: str):
    return await client.post(f"/api/v1/vacancies/{vacancy_uuid}/applications", headers=headers)


async def test_apply_blocked_until_required_test_passed(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905131010")
    test = await create_company_test(client, ctx)
    filial = await _filial(client, ctx)
    vacancy_uuid, out = await _active_vacancy(client, ctx, filial, [test["test_uuid"]])
    assert out["required_test_uuids"] == [test["test_uuid"]]

    worker = await login_user("+79051310103")
    # не прошёл обязательный тест → отклик заблокирован
    assert (await _apply(client, worker["headers"], vacancy_uuid)).status_code == 409

    # прошёл тест → отклик проходит
    await _pass_test(client, worker["headers"], test["test_uuid"])
    assert (await _apply(client, worker["headers"], vacancy_uuid)).status_code == 201


async def test_apply_open_when_no_required_tests(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905131020")
    filial = await _filial(client, ctx)
    vacancy_uuid, out = await _active_vacancy(client, ctx, filial, None)
    assert out["required_test_uuids"] == []

    worker = await login_user("+79051310203")
    assert (await _apply(client, worker["headers"], vacancy_uuid)).status_code == 201


async def test_required_tests_must_belong_to_company_or_platform(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+7905131030")
    filial = await _filial(client, ctx)
    # чужой случайный uuid как обязательный тест — отклоняется на создании вакансии
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies",
        json={
            "filial_uuid": filial,
            "role_name": "Официант",
            "event_title": "Банкет",
            "starts_at": "2026-07-12T16:00:00+03:00",
            "ends_at": "2026-07-12T23:00:00+03:00",
            "venue_address": "Тверская, 9",
            "pay_hour_kop": 45_000,
            "slots": 1,
            "required_test_uuids": ["019f2f4e-0000-7000-8000-000000000000"],
        },
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 422, resp.text
