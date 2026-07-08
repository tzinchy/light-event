from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from app.core.deps import get_current_user, get_session
from app.core.errors import DomainError
from app.mailing.service import MailingService
from app.user.models import User
from app.user.repo import UserRepo
from app.user.schemas import EmailConfirmIn, EmailRequestIn, UserOut, UserUpdateIn, WorkerPublicOut
from app.user.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


async def _viewer_can_see_profile(session: AsyncSession, viewer: User, target_uuid: UUID) -> bool:
    """Профили не публичные (§11.12): сам, админ, либо команда компании, куда человек откликнулся."""
    from sqlalchemy import exists, select

    from app.application.models import Application
    from app.team.models import TeamMember
    from app.user.models import PlatformRole
    from app.vacancy.models import Vacancy

    if viewer.user_uuid == target_uuid or viewer.platform_role == PlatformRole.admin:
        return True
    stmt = select(
        exists().where(
            Application.user_uuid == target_uuid,
            Application.vacancy_uuid == Vacancy.vacancy_uuid,
            Vacancy.company_uuid == TeamMember.company_uuid,
            TeamMember.user_uuid == viewer.user_uuid,
        )
    )
    return bool((await session.execute(stmt)).scalar())


@router.get("/{user_uuid}/public", response_model=WorkerPublicOut)
async def worker_public_profile(
    user_uuid: UUID,
    viewer: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WorkerPublicOut:
    """Профиль соискателя — без контактов; доступ только по отклику (§11.12)."""
    user = await UserRepo(session).get(user_uuid)
    if user is None:
        raise DomainError(404, "Пользователь не найден")
    if not await _viewer_can_see_profile(session, viewer, user_uuid):
        raise DomainError(403, "Профиль виден организациям только после отклика соискателя")
    return WorkerPublicOut.model_validate(user)


def get_user_service(request: Request, session: AsyncSession = Depends(get_session)) -> UserService:
    state = request.app.state
    return UserService(
        session=session,
        settings=state.settings,
        redis=state.redis,
        mailing=MailingService(state.session_factory, state.email_provider),
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
