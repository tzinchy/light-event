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
def settings(pg_container, redis_container, tmp_path_factory) -> Settings:
    from tests import helpers

    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)
    helpers.DB_URL = pg_container.get_connection_url()
    return Settings(
        database_url=pg_container.get_connection_url(),
        redis_url=f"redis://{redis_host}:{redis_port}/0",
        app_secret_key="test-secret-key-0123456789abcdef-0123456789abcdef",
        storage_backend="local",
        local_storage_path=str(tmp_path_factory.mktemp("storage")),
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
def email_outbox() -> CapturingSmsProvider:
    # тот же интерфейс send_otp(destination, code) — переиспользуем капчер
    return CapturingSmsProvider()


@pytest.fixture
async def client(settings, apply_migrations, sms_outbox, email_outbox):
    app = create_app(settings, sms_provider=sms_outbox, email_provider=email_outbox)
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
def login_user(client, sms_outbox):
    """Полный вход по OTP через реальное API; возвращает headers/me/tokens."""

    async def _login(phone: str = "+79051234567") -> dict:
        resp = await client.post("/api/v1/auth/otp/request", json={"phone": phone})
        assert resp.status_code == 202, resp.text
        code = sms_outbox.sent[-1][1]
        resp = await client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})
        assert resp.status_code == 200, resp.text
        tokens = resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me = await client.get("/api/v1/auth/me", headers=headers)
        return {"headers": headers, "tokens": tokens, "me": me.json()}

    return _login


@pytest.fixture
def add_team_member(settings):
    """Участник с заданной матрицей прав через реальный repo — инвайт выдаёт только роль, без прав."""
    from uuid import UUID

    from app.core.db import create_session_factory
    from app.team.models import CompanyRole
    from app.team.repo import TeamRepo

    async def _add(company_uuid: str, user_uuid: str, role: str = "manager", **perms) -> None:
        engine = create_engine(settings.database_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            async with session.begin():
                await TeamRepo(session).add_member(
                    company_uuid=UUID(company_uuid),
                    user_uuid=UUID(user_uuid),
                    role=CompanyRole(role),
                    perm_create=perms.get("perm_create", False),
                    perm_hire=perms.get("perm_hire", False),
                    perm_finance=perms.get("perm_finance", False),
                    perm_invite=perms.get("perm_invite", False),
                )
        await engine.dispose()

    return _add


@pytest.fixture
def expire_invite(settings):
    """Перевод срока действия инвайта в прошлое — машину времени в тестах заменяет прямое UPDATE."""
    from sqlalchemy import text

    async def _expire(invite_link_uuid: str) -> None:
        engine = create_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE invite_link SET expires_at = now() - interval '1 hour' WHERE invite_link_uuid = :u"),
                {"u": invite_link_uuid},
            )
        await engine.dispose()

    return _expire


@pytest.fixture
def make_admin(settings):
    """Бутстрап админа: до этапа админки роль назначается напрямую в БД."""
    from sqlalchemy import text

    async def _make(user_uuid: str) -> None:
        engine = create_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.execute(
                text('UPDATE "user" SET platform_role = \'admin\' WHERE user_uuid = :u'),
                {"u": user_uuid},
            )
        await engine.dispose()

    return _make
