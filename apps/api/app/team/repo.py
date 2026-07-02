from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.team.models import CompanyRole, TeamMember


class TeamRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_membership(self, user_uuid: UUID, company_uuid: UUID) -> TeamMember | None:
        result = await self.session.execute(
            select(TeamMember).where(
                TeamMember.user_uuid == user_uuid, TeamMember.company_uuid == company_uuid
            )
        )
        return result.scalar_one_or_none()

    async def list_by_company(self, company_uuid: UUID) -> list[TeamMember]:
        result = await self.session.execute(
            select(TeamMember).where(TeamMember.company_uuid == company_uuid).order_by(TeamMember.team_member_uuid)
        )
        return list(result.scalars())

    async def add_member(
        self,
        company_uuid: UUID,
        user_uuid: UUID,
        role: CompanyRole,
        *,
        filial_uuid: UUID | None = None,
        email: str | None = None,
        perm_create: bool = False,
        perm_hire: bool = False,
        perm_finance: bool = False,
        perm_invite: bool = False,
    ) -> TeamMember:
        member = TeamMember(
            company_uuid=company_uuid,
            user_uuid=user_uuid,
            company_role=role,
            filial_uuid=filial_uuid,
            email=email,
            perm_create=perm_create,
            perm_hire=perm_hire,
            perm_finance=perm_finance,
            perm_invite=perm_invite,
        )
        self.session.add(member)
        await self.session.flush()
        return member
