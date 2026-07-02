from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.invite.models import InviteLink
from app.team.models import CompanyRole


class InviteRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        company_uuid: UUID,
        filial_uuid: UUID | None,
        role: CompanyRole,
        code: str,
        expires_at: datetime,
        max_uses: int,
        created_by_uuid: UUID,
    ) -> InviteLink:
        invite = InviteLink(
            company_uuid=company_uuid,
            filial_uuid=filial_uuid,
            company_role=role,
            code=code,
            expires_at=expires_at,
            max_uses=max_uses,
            created_by_uuid=created_by_uuid,
        )
        self.session.add(invite)
        await self.session.flush()
        return invite

    async def get(self, invite_link_uuid: UUID) -> InviteLink | None:
        return await self.session.get(InviteLink, invite_link_uuid)

    async def get_by_code_for_update(self, code: str) -> InviteLink | None:
        # блокировка строки: параллельные accept не превысят max_uses
        result = await self.session.execute(
            select(InviteLink).where(InviteLink.code == code).with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_by_company(self, company_uuid: UUID) -> list[InviteLink]:
        result = await self.session.execute(
            select(InviteLink)
            .where(InviteLink.company_uuid == company_uuid)
            .order_by(InviteLink.invite_link_uuid)
        )
        return list(result.scalars())
