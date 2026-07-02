from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.company.models import Company
from app.company.repo import CompanyRepo
from app.company.schemas import CompanyCreateIn, CompanyUpdateIn
from app.core.errors import DomainError
from app.core.permissions import ensure_main_manager
from app.team.models import CompanyRole, TeamMember
from app.team.repo import TeamRepo
from app.user.models import User


class CompanyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.companies = CompanyRepo(session)
        self.team = TeamRepo(session)

    async def create(self, user: User, data: CompanyCreateIn) -> Company:
        company = await self.companies.create(name=data.name, description=data.description)
        # создатель кабинета — main_manager с полным доступом (skill rbac-permissions)
        await self.team.add_member(
            company_uuid=company.company_uuid,
            user_uuid=user.user_uuid,
            role=CompanyRole.main_manager,
            perm_create=True,
            perm_hire=True,
            perm_finance=True,
            perm_invite=True,
        )
        return company

    async def get(self, company_uuid: UUID) -> Company:
        company = await self.companies.get(company_uuid)
        if company is None:
            raise DomainError(404, "Компания не найдена")
        return company

    async def update(self, user: User, company_uuid: UUID, data: CompanyUpdateIn) -> Company:
        await ensure_main_manager(self.session, user, company_uuid)
        company = await self.get(company_uuid)
        if data.name is not None:
            company.name = data.name
        if data.description is not None:
            company.description = data.description
        await self.session.flush()
        return company

    async def list_team(self, company_uuid: UUID) -> list[TeamMember]:
        return await self.team.list_by_company(company_uuid)
