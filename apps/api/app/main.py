from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.core import health
from app.core.config import Settings, get_settings
from app.core.db import create_engine, create_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.engine = create_engine(settings.database_url)
        app.state.session_factory = create_session_factory(app.state.engine)
        app.state.redis = aioredis.from_url(settings.redis_url)
        yield
        await app.state.redis.aclose()
        await app.state.engine.dispose()

    app = FastAPI(title="light-event API", lifespan=lifespan)
    app.include_router(health.router)
    return app


app = create_app()
