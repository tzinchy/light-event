from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.company.models import Company, CompanyStatus
from app.company.repo import CompanyRepo
from app.core.errors import DomainError


class AdminCompanyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.companies = CompanyRepo(session)

    async def list_by_status(self, status: CompanyStatus) -> list[Company]:
        return await self.companies.list_by_status(status)

    async def _get(self, company_uuid: UUID) -> Company:
        company = await self.companies.get(company_uuid)
        if company is None:
            raise DomainError(404, "Компания не найдена")
        return company

    async def verify(self, company_uuid: UUID) -> Company:
        company = await self._get(company_uuid)
        company.status = CompanyStatus.verified
        company.verified_at = datetime.now(timezone.utc)
        company.reject_reason = None
        await self.session.flush()
        return company

    async def reject(self, company_uuid: UUID, reason: str) -> Company:
        company = await self._get(company_uuid)
        company.status = CompanyStatus.rejected
        company.verified_at = None
        company.reject_reason = reason
        await self.session.flush()
        return company
