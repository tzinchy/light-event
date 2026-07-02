from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.company.models import Company
from app.team.models import TeamMember


class CompanyRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, company_uuid: UUID) -> Company | None:
        return await self.session.get(Company, company_uuid)

    async def list_for_user(self, user_uuid: UUID) -> list[tuple[Company, TeamMember]]:
        result = await self.session.execute(
            select(Company, TeamMember)
            .join(TeamMember, TeamMember.company_uuid == Company.company_uuid)
            .where(TeamMember.user_uuid == user_uuid)
            .order_by(TeamMember.team_member_uuid)
        )
        return [(company, member) for company, member in result.all()]

    async def create(self, name: str, description: str | None = None) -> Company:
        company = Company(name=name, description=description)
        self.session.add(company)
        await self.session.flush()
        return company
