from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.company.models import Company
from app.company.schemas import CompanyOut
from app.core.errors import DomainError
from app.favorite.repo import FavoriteRepo
from app.user.models import User


class FavoriteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FavoriteRepo(session)

    async def follow(self, actor: User, company_uuid: UUID) -> None:
        if await self.session.get(Company, company_uuid) is None:
            raise DomainError(404, "Компания не найдена")
        if await self.repo.get(actor.user_uuid, company_uuid) is None:  # идемпотентно
            self.repo.add(actor.user_uuid, company_uuid)
            await self.session.flush()

    async def unfollow(self, actor: User, company_uuid: UUID) -> None:
        await self.repo.remove(actor.user_uuid, company_uuid)
        await self.session.flush()

    async def list_companies(self, actor: User) -> list[CompanyOut]:
        uuids = await self.repo.list_company_uuids(actor.user_uuid)
        if not uuids:
            return []
        result = await self.session.execute(select(Company).where(Company.company_uuid.in_(uuids)))
        by_id = {c.company_uuid: c for c in result.scalars()}
        return [CompanyOut.model_validate(by_id[u]) for u in uuids if u in by_id]
