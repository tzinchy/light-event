from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.pricing.models import ServicePrice


class PricingRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str, company_uuid: UUID | None = None) -> ServicePrice | None:
        result = await self.session.execute(
            select(ServicePrice).where(
                ServicePrice.key == key,
                ServicePrice.company_uuid == company_uuid
                if company_uuid is not None
                else ServicePrice.company_uuid.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def all(self, company_uuid: UUID | None = None) -> dict[str, int]:
        result = await self.session.execute(
            select(ServicePrice).where(
                ServicePrice.company_uuid == company_uuid
                if company_uuid is not None
                else ServicePrice.company_uuid.is_(None)
            )
        )
        return {row.key: row.amount_kop for row in result.scalars()}

    async def upsert(self, key: str, amount_kop: int, company_uuid: UUID | None = None) -> ServicePrice:
        row = await self.get(key, company_uuid)
        if row is None:
            row = ServicePrice(key=key, amount_kop=amount_kop, company_uuid=company_uuid)
            self.session.add(row)
        else:
            row.amount_kop = amount_kop
        await self.session.flush()
        return row
