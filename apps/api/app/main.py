import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.admin import router as admin_router
from app.application import router as application_router
from app.auth import router as auth_router
from app.balance import router as balance_router
from app.candidate_list import router as candidate_list_router
from app.company import router as company_router
from app.core import health
from app.document import router as document_router
from app.filial import router as filial_router
from app.invite import router as invite_router
from app.review import router as review_router
from app.team import router as team_router
from app.test import router as test_router
from app.user import router as user_router
from app.vacancy import router as vacancy_router
from app.core.config import Settings, get_settings
from app.core.db import create_engine, create_session_factory
from app.core.errors import DomainError, domain_error_handler
from app.core.email import EmailProvider, build_email_provider
from app.core.sms import SmsProvider, build_sms_provider
from app.core.storage import build_storage


def create_app(
    settings: Settings | None = None,
    sms_provider: SmsProvider | None = None,
    email_provider: EmailProvider | None = None,
) -> FastAPI:
    # uvicorn настраивает только свои логгеры; без root-хендлера INFO приложения
    # (в т.ч. OTP-коды ConsoleSmsProvider) не попадает в консоль
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")
    settings = settings or get_settings()
    sms = sms_provider or build_sms_provider(settings)
    email = email_provider or build_email_provider(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.engine = create_engine(settings.database_url)
        app.state.session_factory = create_session_factory(app.state.engine)
        app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        app.state.sms_provider = sms
        app.state.email_provider = email
        app.state.storage = await build_storage(settings)
        yield
        await app.state.redis.aclose()
        await app.state.engine.dispose()

    app = FastAPI(title="light-event API", lifespan=lifespan)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.include_router(health.router)
    app.include_router(auth_router.router)
    app.include_router(user_router.router)
    app.include_router(document_router.router)
    app.include_router(company_router.router)
    app.include_router(filial_router.router)
    app.include_router(team_router.router)
    app.include_router(invite_router.router)
    app.include_router(review_router.router)
    app.include_router(balance_router.router)
    app.include_router(vacancy_router.router)
    app.include_router(application_router.router)
    app.include_router(candidate_list_router.router)
    app.include_router(test_router.router)
    app.include_router(admin_router.router)
    return app


app = create_app()
