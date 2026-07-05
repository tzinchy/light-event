"""У вакансии есть свободное описание «О событии» (PLAN §5)."""

from tests.test.test_tests import setup_company


async def test_vacancy_carries_description(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+790582200")
    filial = (
        await client.post(
            f"/api/v1/companies/{ctx['company_uuid']}/filials",
            json={"name": "Тверская", "address": "Тверская, 9"},
            headers=ctx["owner"]["headers"],
        )
    ).json()["filial_uuid"]

    about = "Обслуживание свадебного банкета на 120 гостей, дресс-код чёрный низ / белый верх."
    resp = await client.post(
        f"/api/v1/companies/{ctx['company_uuid']}/vacancies",
        json={
            "filial_uuid": filial,
            "role_name": "Официант",
            "event_title": "Свадебный банкет",
            "description": about,
            "starts_at": "2026-07-12T16:00:00+03:00",
            "ends_at": "2026-07-12T23:00:00+03:00",
            "venue_address": "Тверская, 9",
            "pay_hour_kop": 45_000,
            "slots": 1,
        },
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["description"] == about


async def test_description_optional(client, login_user, make_admin):
    ctx = await setup_company(client, login_user, make_admin, "+790582210")
    filial = (
        await client.post(
            f"/api/v1/companies/{ctx['company_uuid']}/filials",
            json={"name": "Тверская", "address": "Тверская, 9"},
            headers=ctx["owner"]["headers"],
        )
    ).json()["filial_uuid"]
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
        },
        headers=ctx["owner"]["headers"],
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["description"] is None
