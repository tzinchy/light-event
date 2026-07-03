"""Общие хелперы тестов.

Компании создаются через реальное API; подтверждение заявки в модульных тестах —
бутстрап напрямую в БД (сам флоу модерации покрыт tests/admin/test_company_moderation.py).
"""

from sqlalchemy import text

from app.core.db import create_engine

# заполняется session-фикстурой settings в conftest.py
DB_URL: str | None = None

VALID_COMPANY_APPLICATION = {
    "name": "Гранд Холл",
    "description": None,
    "inn": "7707083893",
    "ogrn": "1027700132195",
    "address": "Москва, Тверская, 1",
    "lat": 55.7558,
    "lon": 37.6173,
    "contact_phone": "+79051234567",
}


async def create_company(client, headers, *, name: str = "Гранд Холл") -> dict:
    resp = await client.post(
        "/api/v1/companies", json={**VALID_COMPANY_APPLICATION, "name": name}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_verified_company(client, headers, *, name: str = "Гранд Холл") -> dict:
    company = await create_company(client, headers, name=name)
    assert DB_URL is not None, "фикстура settings ещё не инициализирована"
    engine = create_engine(DB_URL)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE company SET status = 'verified', verified_at = now() WHERE company_uuid = :c"),
            {"c": company["company_uuid"]},
        )
    await engine.dispose()
    company["status"] = "verified"
    return company
