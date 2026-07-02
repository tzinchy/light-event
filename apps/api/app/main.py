from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.auth import router as auth_router
from app.core import health
from app.core.config import Settings, get_settings
from app.core.db import create_engine, create_session_factory
from app.core.errors import DomainError, domain_error_handler
from app.core.sms import ConsoleSmsProvider, SmsProvider


def create_app(settings: Settings | None = None, sms_provider: SmsProvider | None = None) -> FastAPI:
    settings = settings or get_settings()
    sms = sms_provider or ConsoleSmsProvider()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.engine = create_engine(settings.database_url)
        app.state.session_factory = create_session_factory(app.state.engine)
        app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        app.state.sms_provider = sms
        yield
        await app.state.redis.aclose()
        await app.state.engine.dispose()

    app = FastAPI(title="light-event API", lifespan=lifespan)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.include_router(health.router)
    app.include_router(auth_router.router)
    return app


app = create_app()
