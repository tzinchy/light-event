from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.balance.models import TopupRequest, TopupStatus
from app.payment_account.models import PaymentAccount


def _month_start() -> datetime:
    now = datetime.now(UTC)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class PaymentAccountRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, obj) -> None:
        self.session.add(obj)

    async def get(self, uuid: UUID) -> PaymentAccount | None:
        return await self.session.get(PaymentAccount, uuid)

    async def list_all(self) -> list[PaymentAccount]:
        result = await self.session.execute(
            select(PaymentAccount).order_by(PaymentAccount.is_priority.desc(), PaymentAccount.name)
        )
        return list(result.scalars())

    async def list_active(self) -> list[PaymentAccount]:
        result = await self.session.execute(select(PaymentAccount).where(PaymentAccount.active.is_(True)))
        return list(result.scalars())

    async def clear_priority(self) -> None:
        await self.session.execute(update(PaymentAccount).values(is_priority=False))

    async def received_this_month(self, account_uuid: UUID) -> int:
        """Направленный на счёт оборот текущего месяца — pending + approved (не rejected)."""
        result = await self.session.execute(
            select(func.coalesce(func.sum(TopupRequest.amount_kop), 0)).where(
                TopupRequest.payment_account_uuid == account_uuid,
                TopupRequest.status != TopupStatus.rejected,
                TopupRequest.created_at >= _month_start(),
            )
        )
        return int(result.scalar_one())
