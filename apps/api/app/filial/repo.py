from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filial.models import Filial


class FilialRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, filial_uuid: UUID) -> Filial | None:
        return await self.session.get(Filial, filial_uuid)

    async def list_by_company(self, company_uuid: UUID) -> list[Filial]:
        result = await self.session.execute(
            select(Filial).where(Filial.company_uuid == company_uuid).order_by(Filial.filial_uuid)
        )
        return list(result.scalars())

    async def create(self, company_uuid: UUID, name: str, address: str, lat: float | None, lon: float | None) -> Filial:
        filial = Filial(company_uuid=company_uuid, name=name, address=address, lat=lat, lon=lon)
        self.session.add(filial)
        await self.session.flush()
        return filial

    async def delete(self, filial: Filial) -> None:
        await self.session.delete(filial)
        await self.session.flush()
