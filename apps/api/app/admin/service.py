from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.repo import AdminOverviewRepo
from app.admin.schemas import ModerationRequestOut, OverviewOut
from app.company.models import Company, CompanyStatus
from app.company.repo import CompanyRepo
from app.core.errors import DomainError
from app.test.repo import TestRepo
from app.vacancy.repo import VacancyRepo


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


class AdminQueueService:
    """Единая очередь модерации (PLAN §11.1): pending-вакансии и pending-тесты."""

    def __init__(self, session: AsyncSession):
        self.vacancies = VacancyRepo(session)
        self.tests = TestRepo(session)

    async def list_requests(self) -> list[ModerationRequestOut]:
        items = [
            ModerationRequestOut(
                kind="vacancy",
                ref_uuid=vacancy.vacancy_uuid,
                title=vacancy.event_title,
                company_uuid=vacancy.company_uuid,
                company_name=company_name,
                submitted_at=vacancy.updated_at,
            )
            for vacancy, company_name in await self.vacancies.list_pending_moderation()
        ] + [
            ModerationRequestOut(
                kind="test",
                ref_uuid=test.test_uuid,
                title=test.title,
                company_uuid=test.company_uuid,
                company_name=company_name,
                submitted_at=test.updated_at,
            )
            for test, company_name in await self.tests.list_pending_moderation()
        ]
        return sorted(items, key=lambda i: i.submitted_at)


class AdminOverviewService:
    def __init__(self, session: AsyncSession):
        self.repo = AdminOverviewRepo(session)

    async def overview(self) -> OverviewOut:
        users = await self.repo.users_count()
        verified = await self.repo.users_with_verified_docs()
        queues = await self.repo.queue_counts()
        return OverviewOut(
            users_count=users,
            kyc_verified_pct=round(verified * 100 / users, 1) if users else 0.0,
            turnover_kop=await self.repo.turnover_kop(),
            open_complaints=queues["complaints"],
            queues=queues,
        )
