import pytest
import redis.asyncio as aioredis
from alembic import command
from alembic.config import Config as AlembicConfig
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

import app.models_registry  # noqa: F401 — наполняет Base.metadata для очистки таблиц
from app.core.config import Settings
from app.core.db import Base, create_engine
from app.main import create_app


class CapturingSmsProvider:
    """Тестовая реализация SmsProvider: складывает отправленные коды, наружу ничего не шлёт."""

    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    async def send_otp(self, phone: str, code: str) -> None:
        self.sent.append((phone, code))


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:18-alpine", driver="asyncpg") as pg:
        yield pg


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:8-alpine") as rd:
        yield rd


@pytest.fixture(scope="session")
def settings(pg_container, redis_container) -> Settings:
    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)
    return Settings(
        database_url=pg_container.get_connection_url(),
        redis_url=f"redis://{redis_host}:{redis_port}/0",
        app_secret_key="test-secret-key-0123456789abcdef-0123456789abcdef",
        _env_file=None,
    )


@pytest.fixture(scope="session")
def apply_migrations(settings):
    cfg = AlembicConfig("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


@pytest.fixture(autouse=True)
async def clean_state(settings, apply_migrations):
    yield
    engine = create_engine(settings.database_url)
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    await engine.dispose()
    r = aioredis.from_url(settings.redis_url)
    await r.flushdb()
    await r.aclose()


@pytest.fixture
def sms_outbox() -> CapturingSmsProvider:
    return CapturingSmsProvider()


@pytest.fixture
async def client(settings, apply_migrations, sms_outbox):
    app = create_app(settings, sms_provider=sms_outbox)
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
