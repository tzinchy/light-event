from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.balance.models import Account, AccountOwnerType, LedgerEntry, TopupRequest


class BalanceRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_account(self, owner_type: AccountOwnerType, owner_uuid: UUID) -> Account:
        account = await self._get_by_owner(owner_type, owner_uuid)
        if account is not None:
            return account
        try:
            async with self.session.begin_nested():
                account = Account(owner_type=owner_type, owner_uuid=owner_uuid)
                self.session.add(account)
                await self.session.flush()
                return account
        except IntegrityError:
            # параллельное создание — uq_account_owner, перечитываем
            account = await self._get_by_owner(owner_type, owner_uuid)
            assert account is not None
            return account

    async def _get_by_owner(self, owner_type: AccountOwnerType, owner_uuid: UUID) -> Account | None:
        result = await self.session.execute(
            select(Account).where(Account.owner_type == owner_type, Account.owner_uuid == owner_uuid)
        )
        return result.scalar_one_or_none()

    async def lock_accounts(self, *account_uuids: UUID) -> dict[UUID, Account]:
        """Блокировка счетов в детерминированном порядке — против дедлоков (skill money-ledger)."""
        locked: dict[UUID, Account] = {}
        for uuid in sorted(set(account_uuids)):
            result = await self.session.execute(
                select(Account).where(Account.account_uuid == uuid).with_for_update()
            )
            locked[uuid] = result.scalar_one()
        return locked

    def add_ledger_entry(self, entry: LedgerEntry) -> None:
        self.session.add(entry)

    async def list_operations(self, account_uuid: UUID) -> list[LedgerEntry]:
        result = await self.session.execute(
            select(LedgerEntry)
            .where(
                or_(
                    LedgerEntry.debit_account_uuid == account_uuid,
                    LedgerEntry.credit_account_uuid == account_uuid,
                )
            )
            .order_by(LedgerEntry.ledger_entry_uuid.desc())
        )
        return list(result.scalars())

    async def create_topup(self, topup: TopupRequest) -> TopupRequest:
        self.session.add(topup)
        await self.session.flush()
        return topup

    async def get_topup_for_update(self, topup_request_uuid: UUID) -> TopupRequest | None:
        result = await self.session.execute(
            select(TopupRequest)
            .where(TopupRequest.topup_request_uuid == topup_request_uuid)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_topups(self) -> list[TopupRequest]:
        result = await self.session.execute(
            select(TopupRequest).order_by(TopupRequest.topup_request_uuid.desc())
        )
        return list(result.scalars())
