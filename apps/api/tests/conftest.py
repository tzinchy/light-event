import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.core.config import Settings
from app.main import create_app

pytest_plugins = []


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
        app_secret_key="test-secret",
        _env_file=None,
    )


@pytest.fixture(scope="session")
def apply_migrations(settings):
    cfg = AlembicConfig("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


@pytest.fixture
async def client(settings, apply_migrations):
    app = create_app(settings)
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
