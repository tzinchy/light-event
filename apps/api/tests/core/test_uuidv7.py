from sqlalchemy import text

from app.core.db import create_engine


async def test_pk_generated_by_database_is_uuidv7(settings, apply_migrations):
    """PK генерирует сама БД (server_default uuidv7(), PostgreSQL 18) —
    raw INSERT без указания ключа обязан получить UUID версии 7."""
    engine = create_engine(settings.database_url)
    async with engine.begin() as conn:
        row = await conn.execute(
            text(
                "INSERT INTO company "
                "(name, status, inn, ogrn, address, lat, lon, contact_phone, "
                "contact_name, contact_email, contact_position, created_at, updated_at) "
                "VALUES ('ООО Тест', 'pending', '7707083893', '1027700132195', 'Москва, Тверская, 1', "
                "55.75, 37.61, '+79051234567', 'Тест Тестов', 'test@example.com', 'Директор', now(), now()) "
                "RETURNING company_uuid"
            )
        )
        pk = row.scalar_one()
    await engine.dispose()
    assert pk is not None
    assert pk.version == 7
