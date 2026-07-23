from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.repo import AdminOverviewRepo
from app.admin.schemas import AdminUserDetailOut, AdminUserOut, ModerationRequestOut, OverviewOut
from app.company.models import Company, CompanyStatus
from app.company.repo import CompanyRepo
from app.core.errors import DomainError
from app.document.repo import DocumentRepo
from app.test.repo import TestRepo
from app.user.models import ModerationStatus, PlatformRole, User
from app.user.repo import UserRepo
from app.vacancy.repo import VacancyRepo


def _user_out(user: User, documents_count: int = 0) -> AdminUserOut:
    return AdminUserOut.model_validate(user).model_copy(update={"documents_count": documents_count})


def _parse_role(value: str) -> PlatformRole:
    try:
        return PlatformRole(value)
    except ValueError:
        raise DomainError(422, "Неизвестная роль")


class AdminCompanyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.companies = CompanyRepo(session)

    async def list_by_status(self, status: CompanyStatus) -> list[Company]:
        return await self.companies.list_by_status(status)

    async def _get(self, company_uuid: UUID) -> Company:
        company = await self.companies.get(company_uuid)
        if company is None:
            raise DomainError(404, "Компания не найдена")
        return company

    async def verify(self, company_uuid: UUID) -> Company:
        company = await self._get(company_uuid)
        company.status = CompanyStatus.verified
        company.verified_at = datetime.now(timezone.utc)
        company.reject_reason = None
        await self.session.flush()
        return company

    async def reject(self, company_uuid: UUID, reason: str) -> Company:
        company = await self._get(company_uuid)
        company.status = CompanyStatus.rejected
        company.verified_at = None
        company.reject_reason = reason
        await self.session.flush()
        return company


class AdminQueueService:
    """Единая очередь модерации (PLAN §11.1): pending-вакансии и pending-тесты."""

    def __init__(self, session: AsyncSession):
        self.vacancies = VacancyRepo(session)
        self.tests = TestRepo(session)

    async def list_requests(self) -> list[ModerationRequestOut]:
        items = [
            ModerationRequestOut(
                kind="vacancy",
                ref_uuid=vacancy.vacancy_uuid,
                title=vacancy.event_title,
                company_uuid=vacancy.company_uuid,
                company_name=company_name,
                submitted_at=vacancy.updated_at,
            )
            for vacancy, company_name in await self.vacancies.list_pending_moderation()
        ] + [
            ModerationRequestOut(
                kind="test",
                ref_uuid=test.test_uuid,
                title=test.title,
                company_uuid=test.company_uuid,
                company_name=company_name,
                submitted_at=test.updated_at,
            )
            for test, company_name in await self.tests.list_pending_moderation()
        ]
        return sorted(items, key=lambda i: i.submitted_at)


class AdminOverviewService:
    def __init__(self, session: AsyncSession):
        self.repo = AdminOverviewRepo(session)

    async def overview(self) -> OverviewOut:
        users = await self.repo.users_count()
        verified = await self.repo.users_with_verified_docs()
        queues = await self.repo.queue_counts()
        return OverviewOut(
            users_count=users,
            kyc_verified_pct=round(verified * 100 / users, 1) if users else 0.0,
            turnover_kop=await self.repo.turnover_kop(),
            open_complaints=queues["complaints"],
            queues=queues,
        )


class AdminUserService:
    """Модерация и управление пользователями (PLAN §11.15). Только admin (гейт на роутере)."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepo(session)
        self.documents = DocumentRepo(session)

    async def list_users(
        self, *, status: ModerationStatus | None, query: str | None, limit: int, offset: int
    ) -> list[AdminUserOut]:
        rows = await self.users.list_for_admin(status=status, query=query, limit=limit, offset=offset)
        return [_user_out(user, count) for user, count in rows]

    async def _get(self, user_uuid: UUID) -> User:
        user = await self.users.get(user_uuid)
        if user is None:
            raise DomainError(404, "Пользователь не найден")
        return user

    async def detail(self, user_uuid: UUID) -> AdminUserDetailOut:
        user = await self._get(user_uuid)
        docs = await self.documents.list_by_owner(user_uuid)
        base = _user_out(user, len(docs))
        return AdminUserDetailOut(**base.model_dump(), documents=docs)

    async def _moderate(
        self, admin: User, user_uuid: UUID, status: ModerationStatus, *, is_active: bool, reason: str | None
    ) -> AdminUserOut:
        if user_uuid == admin.user_uuid:
            raise DomainError(400, "Нельзя менять модерацию собственной учётной записи")
        user = await self._get(user_uuid)
        user.moderation_status = status
        user.moderation_reason = reason
        user.is_active = is_active
        user.moderated_by_uuid = admin.user_uuid
        user.moderated_at = datetime.now(timezone.utc)
        await self.session.flush()
        # ponytail: уведомление юзеру (notification + письмо) — добавить, когда понадобится клиенту
        return _user_out(user)

    async def approve(self, admin: User, user_uuid: UUID) -> AdminUserOut:
        return await self._moderate(admin, user_uuid, ModerationStatus.approved, is_active=True, reason=None)

    async def resubmit(self, admin: User, user_uuid: UUID, reason: str) -> AdminUserOut:
        return await self._moderate(admin, user_uuid, ModerationStatus.resubmit, is_active=True, reason=reason)

    async def ban(self, admin: User, user_uuid: UUID, reason: str) -> AdminUserOut:
        return await self._moderate(admin, user_uuid, ModerationStatus.banned, is_active=False, reason=reason)

    async def unban(self, admin: User, user_uuid: UUID) -> AdminUserOut:
        return await self._moderate(admin, user_uuid, ModerationStatus.approved, is_active=True, reason=None)

    async def update(self, admin: User, user_uuid: UUID, *, platform_role: str | None, name: str | None) -> AdminUserOut:
        user = await self._get(user_uuid)
        if platform_role is not None:
            if user_uuid == admin.user_uuid:
                raise DomainError(400, "Нельзя менять собственную роль")
            user.platform_role = _parse_role(platform_role)
        if name is not None:
            user.name = name
        await self.session.flush()
        return _user_out(user)

    async def create(self, *, email: str, platform_role: str) -> AdminUserOut:
        if await self.users.get_by_email(email) is not None:
            raise DomainError(409, "Пользователь с такой почтой уже существует")
        user = await self.users.create_with_email(email)
        user.platform_role = _parse_role(platform_role)
        user.moderation_status = ModerationStatus.approved
        user.moderated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return _user_out(user)
