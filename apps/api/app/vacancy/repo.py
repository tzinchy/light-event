from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.company.models import Company
from app.vacancy.models import Vacancy, VacancyStatus


class VacancyRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, vacancy_uuid: UUID) -> Vacancy | None:
        return await self.session.get(Vacancy, vacancy_uuid)

    async def get_for_update(self, vacancy_uuid: UUID) -> Vacancy | None:
        result = await self.session.execute(
            select(Vacancy).where(Vacancy.vacancy_uuid == vacancy_uuid).with_for_update()
        )
        return result.scalar_one_or_none()

    def add(self, vacancy: Vacancy) -> None:
        self.session.add(vacancy)

    async def list_feed(
        self,
        *,
        role: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[tuple[Vacancy, Company]]:
        query = (
            select(Vacancy, Company)
            .join(Company, Company.company_uuid == Vacancy.company_uuid)
            .where(Vacancy.status == VacancyStatus.active, Vacancy.archived_at.is_(None))
            .order_by(Vacancy.starts_at)
        )
        if role:
            query = query.where(Vacancy.role_name == role)
        if date_from:
            query = query.where(Vacancy.starts_at >= date_from)
        if date_to:
            query = query.where(Vacancy.starts_at <= date_to)
        result = await self.session.execute(query)
        return [(vacancy, company) for vacancy, company in result.all()]

    async def list_by_company(self, company_uuid: UUID) -> list[Vacancy]:
        result = await self.session.execute(
            select(Vacancy)
            .where(Vacancy.company_uuid == company_uuid)
            .order_by(Vacancy.vacancy_uuid.desc())
        )
        return list(result.scalars())
