from typing import AsyncIterator

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import DomainError
from app.core.security import decode_access_token
from app.user.models import User
from app.user.repo import UserRepo

bearer_scheme = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        async with session.begin():
            yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> User:
    if credentials is None:
        raise DomainError(401, "Требуется авторизация")
    try:
        user_uuid = decode_access_token(credentials.credentials, settings.app_secret_key)
    except jwt.InvalidTokenError:
        raise DomainError(401, "Недействительный токен")
    user = await UserRepo(session).get(user_uuid)
    if user is None or not user.is_active:
        raise DomainError(401, "Пользователь не найден или заблокирован")
    return user
