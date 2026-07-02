from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.core.errors import DomainError
from app.team.models import CompanyRole, TeamMember
from app.team.repo import TeamRepo
from app.user.models import PlatformRole, User


async def ensure_membership(session: AsyncSession, user: User, company_uuid: UUID) -> TeamMember:
    member = await TeamRepo(session).get_membership(user.user_uuid, company_uuid)
    if member is None:
        raise DomainError(403, "Вы не состоите в команде этой компании")
    return member


async def ensure_permission(session: AsyncSession, user: User, company_uuid: UUID, perm: str) -> TeamMember:
    member = await ensure_membership(session, user, company_uuid)
    if not member.has_permission(perm):
        raise DomainError(403, "Недостаточно прав для этого действия")
    return member


async def ensure_main_manager(session: AsyncSession, user: User, company_uuid: UUID) -> TeamMember:
    member = await ensure_membership(session, user, company_uuid)
    if member.company_role != CompanyRole.main_manager:
        raise DomainError(403, "Доступно только главному менеджеру")
    return member


def require_member():
    """FastAPI-зависимость: членство в компании из path-параметра company_uuid."""

    async def dep(
        company_uuid: UUID,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> TeamMember:
        return await ensure_membership(session, user, company_uuid)

    return dep


def require_permission(perm: str):
    """FastAPI-зависимость: право perm (create/hire/finance/invite); main_manager проходит всегда."""

    async def dep(
        company_uuid: UUID,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> TeamMember:
        return await ensure_permission(session, user, company_uuid, perm)

    return dep


def require_admin():
    """FastAPI-зависимость: platform_role = admin (модерация, финансы платформы)."""

    async def dep(user: User = Depends(get_current_user)) -> User:
        if user.platform_role != PlatformRole.admin:
            raise DomainError(403, "Доступно только администратору")
        return user

    return dep


def require_main_manager():
    async def dep(
        company_uuid: UUID,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> TeamMember:
        return await ensure_main_manager(session, user, company_uuid)

    return dep
