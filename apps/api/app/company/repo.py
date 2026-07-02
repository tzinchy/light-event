from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.company.models import Company


class CompanyRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, company_uuid: UUID) -> Company | None:
        return await self.session.get(Company, company_uuid)

    async def create(self, name: str, description: str | None = None) -> Company:
        company = Company(name=name, description=description)
        self.session.add(company)
        await self.session.flush()
        return company
