from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.favorite.models import CompanyFavorite


class FavoriteRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_uuid: UUID, company_uuid: UUID) -> CompanyFavorite | None:
        result = await self.session.execute(
            select(CompanyFavorite).where(
                CompanyFavorite.user_uuid == user_uuid, CompanyFavorite.company_uuid == company_uuid
            )
        )
        return result.scalar_one_or_none()

    def add(self, user_uuid: UUID, company_uuid: UUID) -> None:
        self.session.add(CompanyFavorite(user_uuid=user_uuid, company_uuid=company_uuid))

    async def remove(self, user_uuid: UUID, company_uuid: UUID) -> None:
        await self.session.execute(
            delete(CompanyFavorite).where(
                CompanyFavorite.user_uuid == user_uuid, CompanyFavorite.company_uuid == company_uuid
            )
        )

    async def list_company_uuids(self, user_uuid: UUID) -> list[UUID]:
        result = await self.session.execute(
            select(CompanyFavorite.company_uuid)
            .where(CompanyFavorite.user_uuid == user_uuid)
            .order_by(CompanyFavorite.company_favorite_uuid.desc())
        )
        return list(result.scalars())

    async def follower_uuids(self, company_uuid: UUID) -> list[UUID]:
        result = await self.session.execute(
            select(CompanyFavorite.user_uuid).where(CompanyFavorite.company_uuid == company_uuid)
        )
        return list(result.scalars())
