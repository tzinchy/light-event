from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.balance.models import PLATFORM_OWNER_UUID, AccountOwnerType, LedgerKind
from app.balance.repo import BalanceRepo
from app.balance.service import BalanceService
from app.core.config import Settings
from app.core.errors import DomainError
from app.core.permissions import ensure_membership, ensure_permission
from app.filial.repo import FilialRepo
from app.pricing.service import PricingService
from app.test.repo import TestRepo
from app.user.models import User
from app.vacancy.models import Vacancy, VacancyStatus
from app.vacancy.repo import VacancyRepo
from app.vacancy.schemas import ModerateIn, VacancyCreateIn, VacancyUpdateIn


def compute_total_kop(starts_at: datetime, ends_at: datetime, pay_hour_kop: int) -> int:
    hours = (ends_at - starts_at).total_seconds() / 3600
    return round(hours * pay_hour_kop)


class VacancyService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.vacancies = VacancyRepo(session)
        self.filials = FilialRepo(session)
        self.tests = TestRepo(session)
        self.balance = BalanceService(session)

    async def _validate_required_tests(self, company_uuid: UUID, uuids: list[UUID]) -> None:
        assignable = await self.tests.assignable_ids(company_uuid, uuids)
        unknown = set(uuids) - assignable
        if unknown:
            raise DomainError(422, "Обязательным можно сделать только опубликованный тест компании или платформы")

    async def create(self, actor: User, company_uuid: UUID, data: VacancyCreateIn) -> Vacancy:
        member = await ensure_permission(self.session, actor, company_uuid, "create")
        filial = await self.filials.get(data.filial_uuid)
        if filial is None or filial.company_uuid != company_uuid:
            raise DomainError(404, "Филиал не найден в этой компании")
        await self._validate_required_tests(company_uuid, data.required_test_uuids)
        vacancy = Vacancy(
            company_uuid=company_uuid,
            created_by_uuid=member.team_member_uuid,
            pay_total_kop=compute_total_kop(data.starts_at, data.ends_at, data.pay_hour_kop),
            **data.model_dump(),
        )
        self.vacancies.add(vacancy)
        await self.session.flush()
        return vacancy

    async def get(self, vacancy_uuid: UUID) -> Vacancy:
        vacancy = await self.vacancies.get(vacancy_uuid)
        if vacancy is None:
            raise DomainError(404, "Смена не найдена")
        return vacancy

    async def update(self, actor: User, vacancy_uuid: UUID, data: VacancyUpdateIn) -> Vacancy:
        vacancy = await self.get(vacancy_uuid)
        await ensure_permission(self.session, actor, vacancy.company_uuid, "create")
        if vacancy.status != VacancyStatus.draft:
            raise DomainError(409, "Редактировать можно только черновик")
        if data.required_test_uuids is not None:
            await self._validate_required_tests(vacancy.company_uuid, data.required_test_uuids)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(vacancy, field, value)
        vacancy.pay_total_kop = compute_total_kop(vacancy.starts_at, vacancy.ends_at, vacancy.pay_hour_kop)
        await self.session.flush()
        return vacancy

    async def publish(self, actor: User, vacancy_uuid: UUID) -> Vacancy:
        # блокировка строки: параллельный publish не спишет комиссию дважды
        vacancy = await self.vacancies.get_for_update(vacancy_uuid)
        if vacancy is None:
            raise DomainError(404, "Смена не найдена")
        await ensure_permission(self.session, actor, vacancy.company_uuid, "create")
        if vacancy.status != VacancyStatus.draft:
            raise DomainError(409, "Публиковать можно только черновик")
        repo = BalanceRepo(self.session)
        company_account = await repo.get_or_create_account(AccountOwnerType.company, vacancy.company_uuid)
        platform_account = await repo.get_or_create_account(AccountOwnerType.platform, PLATFORM_OWNER_UUID)
        # списание платы за публикацию и смена статуса — одна транзакция: при нехватке средств всё откатывается
        await self.balance.transfer(
            debit_account_uuid=company_account.account_uuid,
            credit_account_uuid=platform_account.account_uuid,
            amount_kop=await PricingService(self.session, self.settings).fee("vacancy_publish"),
            kind=LedgerKind.vacancy_fee,
            ref_type="vacancy",
            ref_uuid=vacancy.vacancy_uuid,
            comment=f"Публикация смены · {vacancy.event_title}",
        )
        vacancy.status = VacancyStatus.pending_moderation
        await self.session.flush()
        return vacancy

    async def archive(self, actor: User, vacancy_uuid: UUID) -> Vacancy:
        vacancy = await self.get(vacancy_uuid)
        await ensure_permission(self.session, actor, vacancy.company_uuid, "create")
        if vacancy.archived_at is None:
            vacancy.archived_at = datetime.now(UTC)
            await self.session.flush()
        return vacancy

    async def moderate(self, admin: User, vacancy_uuid: UUID, data: ModerateIn) -> Vacancy:
        vacancy = await self.vacancies.get_for_update(vacancy_uuid)
        if vacancy is None:
            raise DomainError(404, "Смена не найдена")
        if vacancy.status != VacancyStatus.pending_moderation:
            raise DomainError(409, "Смена не находится на модерации")
        if data.action == "approve":
            vacancy.status = VacancyStatus.active
        else:
            vacancy.status = VacancyStatus.rejected
            vacancy.reject_reason = data.reason
        await self.session.flush()
        return vacancy

    async def feed(self, *, role: str | None, date_from: datetime | None, date_to: datetime | None):
        return await self.vacancies.list_feed(role=role, date_from=date_from, date_to=date_to)

    async def list_by_company(self, actor: User, company_uuid: UUID) -> list[Vacancy]:
        await ensure_membership(self.session, actor, company_uuid)
        return await self.vacancies.list_by_company(company_uuid)
