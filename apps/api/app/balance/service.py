from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.balance.models import (
    PLATFORM_OWNER_UUID,
    Account,
    AccountOwnerType,
    LedgerEntry,
    LedgerKind,
    Payout,
    PayoutStatus,
    TopupRequest,
    TopupStatus,
)
from app.balance.repo import BalanceRepo
from app.balance.schemas import OperationOut, TopupCreateIn, TopupResolveIn
from app.core.config import get_settings
from app.core.errors import DomainError
from app.core.permissions import ensure_permission
from app.document.models import DocumentKind
from app.document.repo import DocumentRepo
from app.application.models import ApplicationStatus
from app.user.models import User


class BalanceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BalanceRepo(session)
        self.documents = DocumentRepo(session)

    # --- ledger-примитив: единственная точка движения денег -----------------

    async def transfer(
        self,
        *,
        debit_account_uuid: UUID,
        credit_account_uuid: UUID,
        amount_kop: int,
        kind: LedgerKind,
        ref_type: str | None = None,
        ref_uuid: UUID | None = None,
        comment: str | None = None,
        from_hold: bool = False,
    ) -> LedgerEntry:
        """Двойная запись: дебет → кредит одной транзакцией с блокировкой обоих счетов.

        from_hold=True — дебет из резерва (on_hold) вместо доступных средств (выплаты по сменам).
        """
        if amount_kop <= 0:
            raise DomainError(422, "Сумма операции должна быть больше нуля")
        locked = await self.repo.lock_accounts(debit_account_uuid, credit_account_uuid)
        debit, credit = locked[debit_account_uuid], locked[credit_account_uuid]
        if from_hold:
            if debit.on_hold_kop < amount_kop:
                raise DomainError(409, "В резерве недостаточно средств")
            debit.on_hold_kop -= amount_kop
        else:
            # счёт платформы — зеркало внешних денег, может уходить в минус (topup)
            if debit.owner_type != AccountOwnerType.platform and debit.available_kop < amount_kop:
                raise DomainError(409, "Недостаточно средств на счёте")
            debit.available_kop -= amount_kop
        credit.available_kop += amount_kop
        entry = LedgerEntry(
            debit_account_uuid=debit_account_uuid,
            credit_account_uuid=credit_account_uuid,
            amount_kop=amount_kop,
            kind=kind,
            ref_type=ref_type,
            ref_uuid=ref_uuid,
            comment=comment,
        )
        self.repo.add_ledger_entry(entry)
        await self.session.flush()
        return entry

    # --- счёт компании -------------------------------------------------------

    async def get_company_account(self, actor: User, company_uuid: UUID) -> Account:
        await ensure_permission(self.session, actor, company_uuid, "finance")
        return await self.repo.get_or_create_account(AccountOwnerType.company, company_uuid)

    async def list_company_operations(self, actor: User, company_uuid: UUID) -> list[OperationOut]:
        account = await self.get_company_account(actor, company_uuid)
        entries = await self.repo.list_operations(account.account_uuid)
        return [
            OperationOut(
                ledger_entry_uuid=e.ledger_entry_uuid,
                kind=e.kind,
                amount_kop=e.amount_kop,
                direction="in" if e.credit_account_uuid == account.account_uuid else "out",
                comment=e.comment,
                created_at=e.created_at,
            )
            for e in entries
        ]

    # --- пополнение: заявка → ручное подтверждение админом -------------------

    async def create_topup_request(self, actor: User, company_uuid: UUID, data: TopupCreateIn) -> TopupRequest:
        account = await self.get_company_account(actor, company_uuid)
        proof = await self.documents.get(data.proof_document_uuid)
        if proof is None or proof.owner_uuid != actor.user_uuid or proof.kind != DocumentKind.payment_proof:
            raise DomainError(404, "Пруф платежа не найден среди ваших документов")
        return await self.repo.create_topup(
            TopupRequest(
                account_uuid=account.account_uuid,
                amount_kop=data.amount_kop,
                proof_document_uuid=data.proof_document_uuid,
                payment_details=data.payment_details,
            )
        )

    async def list_topup_requests(self) -> list[TopupRequest]:
        return await self.repo.list_topups()

    async def resolve_topup(self, admin: User, topup_request_uuid: UUID, data: TopupResolveIn) -> TopupRequest:
        topup = await self.repo.get_topup_for_update(topup_request_uuid)
        if topup is None:
            raise DomainError(404, "Заявка на пополнение не найдена")
        if topup.status != TopupStatus.pending:
            raise DomainError(409, "Заявка уже рассмотрена")
        if data.action == "approve":
            platform = await self.repo.get_or_create_account(AccountOwnerType.platform, PLATFORM_OWNER_UUID)
            await self.transfer(
                debit_account_uuid=platform.account_uuid,
                credit_account_uuid=topup.account_uuid,
                amount_kop=topup.amount_kop,
                kind=LedgerKind.topup,
                ref_type="topup_request",
                ref_uuid=topup.topup_request_uuid,
                comment="Пополнение счёта (подтверждено администратором)",
            )
            topup.status = TopupStatus.approved
        else:
            topup.status = TopupStatus.rejected
            topup.reject_reason = data.reason
        topup.reviewed_by_uuid = admin.user_uuid
        topup.reviewed_at = datetime.now(UTC)
        await self.session.flush()
        return topup

    # --- payout-цикл: резерв при подтверждении, проведение админом ------------

    async def reserve_for_shift(self, vacancy) -> Payout:
        """Подтверждение соискателя: итог за смену уходит в резерв (on_hold).

        Движение внутри одного счёта в журнал не пишется (двойная запись —
        только между счетами); резерв сверяется по открытым payout.
        """
        account = await self.repo.get_or_create_account(AccountOwnerType.company, vacancy.company_uuid)
        locked = await self.repo.lock_accounts(account.account_uuid)
        account = locked[account.account_uuid]
        amount_kop = vacancy.pay_total_kop
        if account.available_kop < amount_kop:
            raise DomainError(409, "Недостаточно средств для резерва под выплату — пополните счёт")
        account.available_kop -= amount_kop
        account.on_hold_kop += amount_kop
        payout = await self.repo.get_or_create_pending_payout(vacancy.vacancy_uuid, vacancy.company_uuid)
        payout.workers_count += 1
        payout.amount_kop += amount_kop
        await self.session.flush()
        return payout

    async def list_company_payouts(self, actor: User, company_uuid: UUID) -> list[Payout]:
        await ensure_permission(self.session, actor, company_uuid, "finance")
        return await self.repo.list_payouts_by_company(company_uuid)

    async def list_pending_payouts(self) -> list[Payout]:
        return await self.repo.list_pending_payouts()

    async def execute_payout(self, admin: User, payout_uuid: UUID) -> Payout:
        """Проведение выплаты: из резерва компании — соискателям (94%) и платформе (6%)."""
        from app.application.models import ApplicationEvent, ApplicationEventKind
        from app.application.repo import ApplicationRepo
        from app.vacancy.repo import VacancyRepo

        payout = await self.repo.get_payout_for_update(payout_uuid)
        if payout is None:
            raise DomainError(404, "Выплата не найдена")
        if payout.status != PayoutStatus.pending:
            raise DomainError(409, "Выплата уже проведена")

        vacancy = await VacancyRepo(self.session).get(payout.vacancy_uuid)
        applications = await ApplicationRepo(self.session).list_confirmed_for_update(payout.vacancy_uuid)
        company_account = await self.repo.get_or_create_account(AccountOwnerType.company, payout.company_uuid)
        platform_account = await self.repo.get_or_create_account(AccountOwnerType.platform, PLATFORM_OWNER_UUID)

        pct = get_settings().platform_commission_pct
        for application in applications:
            commission_kop = vacancy.pay_total_kop * pct // 100
            worker_account = await self.repo.get_or_create_account(AccountOwnerType.user, application.user_uuid)
            await self.transfer(
                debit_account_uuid=company_account.account_uuid,
                credit_account_uuid=worker_account.account_uuid,
                amount_kop=vacancy.pay_total_kop - commission_kop,
                kind=LedgerKind.payout,
                ref_type="application",
                ref_uuid=application.application_uuid,
                comment="Выплата за смену",
                from_hold=True,
            )
            await self.transfer(
                debit_account_uuid=company_account.account_uuid,
                credit_account_uuid=platform_account.account_uuid,
                amount_kop=commission_kop,
                kind=LedgerKind.commission,
                ref_type="payout",
                ref_uuid=payout.payout_uuid,
                comment=f"Комиссия платформы {pct}%",
                from_hold=True,
            )
            application.status = ApplicationStatus.paid
            self.session.add(
                ApplicationEvent(
                    application_uuid=application.application_uuid,
                    kind=ApplicationEventKind.payout,
                    actor_uuid=admin.user_uuid,
                )
            )

        payout.status = PayoutStatus.paid
        payout.paid_at = datetime.now(UTC)
        await self.session.flush()
        return payout
