from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.permissions import ensure_main_manager
from app.team.models import CompanyRole, TeamMember
from app.team.repo import TeamRepo
from app.team.schemas import TeamPermissionsPatchIn
from app.user.models import User


class TeamService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.team = TeamRepo(session)

    async def _get_member(self, team_member_uuid: UUID) -> TeamMember:
        member = await self.team.get(team_member_uuid)
        if member is None:
            raise DomainError(404, "Участник команды не найден")
        return member

    async def update_permissions(
        self, actor: User, team_member_uuid: UUID, data: TeamPermissionsPatchIn
    ) -> TeamMember:
        member = await self._get_member(team_member_uuid)
        # права выдаёт только main_manager (skill rbac-permissions)
        await ensure_main_manager(self.session, actor, member.company_uuid)
        if member.company_role == CompanyRole.main_manager:
            raise DomainError(403, "У главного менеджера всегда полный доступ — права изменить нельзя")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(member, field, value)
        await self.session.flush()
        return member

    async def remove_member(self, actor: User, team_member_uuid: UUID) -> None:
        member = await self._get_member(team_member_uuid)
        await ensure_main_manager(self.session, actor, member.company_uuid)
        if member.company_role == CompanyRole.main_manager:
            raise DomainError(403, "Главного менеджера нельзя удалить из команды")
        await self.session.delete(member)
        await self.session.flush()
