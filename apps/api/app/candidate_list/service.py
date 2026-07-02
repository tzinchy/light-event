from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.candidate_list.models import CandidateList, CandidateListEntry
from app.candidate_list.repo import CandidateListRepo
from app.candidate_list.schemas import CandidateEntryIn
from app.core.errors import DomainError
from app.core.permissions import ensure_permission
from app.user.models import User
from app.user.repo import UserRepo


class CandidateListService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.entries = CandidateListRepo(session)

    async def put(self, actor: User, company_uuid: UUID, user_uuid: UUID, data: CandidateEntryIn) -> CandidateListEntry:
        await ensure_permission(self.session, actor, company_uuid, "hire")
        if await UserRepo(self.session).get(user_uuid) is None:
            raise DomainError(404, "Пользователь не найден")
        entry = await self.entries.get(company_uuid, user_uuid)
        if entry is None:
            entry = CandidateListEntry(company_uuid=company_uuid, user_uuid=user_uuid, list=CandidateList(data.list))
            self.entries.add(entry)
        else:
            entry.list = CandidateList(data.list)
        entry.note = data.note
        await self.session.flush()
        return entry

    async def list(self, actor: User, company_uuid: UUID, list_filter: str | None) -> list[CandidateListEntry]:
        await ensure_permission(self.session, actor, company_uuid, "hire")
        return await self.entries.list_by_company(
            company_uuid, CandidateList(list_filter) if list_filter else None
        )

    async def delete(self, actor: User, company_uuid: UUID, user_uuid: UUID) -> None:
        await ensure_permission(self.session, actor, company_uuid, "hire")
        entry = await self.entries.get(company_uuid, user_uuid)
        if entry is None:
            raise DomainError(404, "Кандидат не найден в списках")
        await self.entries.delete(entry)
        await self.session.flush()
