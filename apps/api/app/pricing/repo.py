from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.pricing.models import ServicePrice


class PricingRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> ServicePrice | None:
        result = await self.session.execute(select(ServicePrice).where(ServicePrice.key == key))
        return result.scalar_one_or_none()

    async def all(self) -> dict[str, int]:
        result = await self.session.execute(select(ServicePrice))
        return {row.key: row.amount_kop for row in result.scalars()}

    async def upsert(self, key: str, amount_kop: int) -> ServicePrice:
        row = await self.get(key)
        if row is None:
            row = ServicePrice(key=key, amount_kop=amount_kop)
            self.session.add(row)
        else:
            row.amount_kop = amount_kop
        await self.session.flush()
        return row
