from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from app.core.deps import get_current_user, get_session
from app.core.errors import DomainError
from app.user.models import User
from app.user.repo import UserRepo
from app.user.schemas import EmailConfirmIn, EmailRequestIn, UserOut, UserUpdateIn, WorkerPublicOut
from app.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{user_uuid}/public", response_model=WorkerPublicOut)
async def worker_public_profile(
    user_uuid: UUID,
    _viewer: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WorkerPublicOut:
    """Публичный профиль соискателя (для организаций) — без контактов."""
    user = await UserRepo(session).get(user_uuid)
    if user is None:
        raise DomainError(404, "Пользователь не найден")
    return WorkerPublicOut.model_validate(user)


def get_user_service(request: Request, session: AsyncSession = Depends(get_session)) -> UserService:
    state = request.app.state
    return UserService(
        session=session, settings=state.settings, redis=state.redis, email=state.email_provider
    )


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdateIn,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserOut:
    return UserOut.model_validate(await service.update_profile(user, payload))


@router.post("/me/email", status_code=202)
async def request_email_code(
    payload: EmailRequestIn,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict:
    await service.request_email_code(user, payload.email)
    return {"detail": "Код отправлен на почту"}


@router.post("/me/email/confirm", response_model=UserOut)
async def confirm_email(
    payload: EmailConfirmIn,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserOut:
    return UserOut.model_validate(await service.confirm_email(user, payload.code))
