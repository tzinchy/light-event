import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.permissions import ensure_permission
from app.invite.models import InviteLink
from app.invite.repo import InviteRepo
from app.invite.schemas import INVITE_TTL, InviteCreateIn
from app.team.models import CompanyRole, TeamMember
from app.team.repo import TeamRepo
from app.user.models import User


class InviteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.invites = InviteRepo(session)
        self.team = TeamRepo(session)

    async def create(self, actor: User, company_uuid: UUID, data: InviteCreateIn) -> InviteLink:
        member = await ensure_permission(self.session, actor, company_uuid, "invite")
        return await self.invites.create(
            company_uuid=company_uuid,
            filial_uuid=data.filial_uuid,
            role=CompanyRole(data.role),
            code=secrets.token_urlsafe(9),
            expires_at=datetime.now(UTC) + INVITE_TTL[data.expires_in],
            max_uses=data.max_uses,
            created_by_uuid=member.team_member_uuid,
        )

    async def list_for_company(self, actor: User, company_uuid: UUID) -> list[InviteLink]:
        await ensure_permission(self.session, actor, company_uuid, "invite")
        return await self.invites.list_by_company(company_uuid)

    async def accept(self, actor: User, code: str) -> TeamMember:
        invite = await self.invites.get_by_code_for_update(code)
        if invite is None:
            raise DomainError(404, "Пригласительная ссылка не найдена")
        if not invite.active:
            raise DomainError(410, "Ссылка недействительна: отозвана, истекла или лимит переходов исчерпан")
        existing = await self.team.get_membership(actor.user_uuid, invite.company_uuid)
        if existing is not None:
            raise DomainError(409, "Вы уже состоите в команде этой компании")
        # права после вступления выдаёт main_manager — по ссылке только роль
        member = await self.team.add_member(
            company_uuid=invite.company_uuid,
            user_uuid=actor.user_uuid,
            role=invite.company_role,
            filial_uuid=invite.filial_uuid,
        )
        invite.uses_count += 1
        await self.session.flush()
        return member

    async def revoke(self, actor: User, invite_link_uuid: UUID) -> InviteLink:
        invite = await self.invites.get(invite_link_uuid)
        if invite is None:
            raise DomainError(404, "Пригласительная ссылка не найдена")
        await ensure_permission(self.session, actor, invite.company_uuid, "invite")
        if invite.revoked_at is None:
            invite.revoked_at = datetime.now(UTC)
            await self.session.flush()
        return invite
