from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.company_application.models import ApplicationStatus, CompanyApplication


class CompanyApplicationRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **fields) -> CompanyApplication:
        application = CompanyApplication(**fields)
        self.session.add(application)
        await self.session.flush()
        return application

    async def get(self, application_uuid: UUID) -> CompanyApplication | None:
        return await self.session.get(CompanyApplication, application_uuid)

    async def list_by_status(self, status: ApplicationStatus) -> list[CompanyApplication]:
        result = await self.session.execute(
            select(CompanyApplication)
            .where(CompanyApplication.status == status)
            .order_by(CompanyApplication.created_at)
        )
        return list(result.scalars())
