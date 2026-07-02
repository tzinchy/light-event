from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.candidate_list.models import CandidateList, CandidateListEntry


class CandidateListRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, company_uuid: UUID, user_uuid: UUID) -> CandidateListEntry | None:
        result = await self.session.execute(
            select(CandidateListEntry).where(
                CandidateListEntry.company_uuid == company_uuid,
                CandidateListEntry.user_uuid == user_uuid,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_company(
        self, company_uuid: UUID, list_filter: CandidateList | None = None
    ) -> list[CandidateListEntry]:
        query = select(CandidateListEntry).where(CandidateListEntry.company_uuid == company_uuid)
        if list_filter is not None:
            query = query.where(CandidateListEntry.list == list_filter)
        result = await self.session.execute(query.order_by(CandidateListEntry.entry_uuid))
        return list(result.scalars())

    def add(self, entry: CandidateListEntry) -> None:
        self.session.add(entry)

    async def delete(self, entry: CandidateListEntry) -> None:
        await self.session.delete(entry)
