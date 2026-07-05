from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.payment_account.models import PaymentAccount
from app.payment_account.repo import PaymentAccountRepo
from app.payment_account.schemas import PaymentAccountCreateIn, PaymentAccountOut, PaymentAccountUpdateIn


class PaymentAccountService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PaymentAccountRepo(session)

    async def create(self, data: PaymentAccountCreateIn) -> PaymentAccount:
        if data.is_priority:
            await self.repo.clear_priority()
        account = PaymentAccount(
            name=data.name,
            requisites=data.requisites,
            monthly_limit_kop=data.monthly_limit_kop,
            is_priority=data.is_priority,
        )
        self.repo.add(account)
        await self.session.flush()
        return account

    async def update(self, uuid: UUID, data: PaymentAccountUpdateIn) -> PaymentAccount:
        account = await self.repo.get(uuid)
        if account is None:
            raise DomainError(404, "Счёт не найден")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(account, field, value)
        await self.session.flush()
        return account

    async def set_priority(self, uuid: UUID) -> PaymentAccount:
        account = await self.repo.get(uuid)
        if account is None:
            raise DomainError(404, "Счёт не найден")
        await self.repo.clear_priority()
        account.is_priority = True
        await self.session.flush()
        return account

    async def list_with_usage(self) -> list[PaymentAccountOut]:
        out: list[PaymentAccountOut] = []
        for account in await self.repo.list_all():
            item = PaymentAccountOut.model_validate(account)
            item.received_this_month_kop = await self.repo.received_this_month(account.payment_account_uuid)
            out.append(item)
        return out

    async def select_for_amount(self, amount_kop: int) -> PaymentAccount | None:
        """Приоритетный счёт, если влезает в месячный лимит; иначе активный с наибольшим запасом."""
        candidates: list[tuple[PaymentAccount, int]] = []
        for account in await self.repo.list_active():
            remaining = account.monthly_limit_kop - await self.repo.received_this_month(account.payment_account_uuid)
            if remaining >= amount_kop:
                candidates.append((account, remaining))
        if not candidates:
            return None
        for account, _ in candidates:
            if account.is_priority:
                return account
        return max(candidates, key=lambda pair: pair[1])[0]
