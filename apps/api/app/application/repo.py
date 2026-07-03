from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.models import Application, ApplicationEvent, ApplicationStatus
from app.candidate_list.models import CandidateList, CandidateListEntry
from app.company.models import Company
from app.user.models import User
from app.vacancy.models import Vacancy


def _not_blacklisted(company_uuid_col):
    """Фильтр ЧС в repo-слое: скрывает отклики кандидата от компании (skill rbac-permissions)."""
    return ~exists(
        select(CandidateListEntry.entry_uuid).where(
            CandidateListEntry.company_uuid == company_uuid_col,
            CandidateListEntry.user_uuid == Application.user_uuid,
            CandidateListEntry.list == CandidateList.blacklist,
        )
    )


class ApplicationRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, application: Application) -> None:
        self.session.add(application)

    def add_event(self, event: ApplicationEvent) -> None:
        self.session.add(event)

    async def get(self, application_uuid: UUID) -> Application | None:
        return await self.session.get(Application, application_uuid)

    async def get_for_update(self, application_uuid: UUID) -> Application | None:
        result = await self.session.execute(
            select(Application).where(Application.application_uuid == application_uuid).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_vacancy_user(self, vacancy_uuid: UUID, user_uuid: UUID) -> Application | None:
        result = await self.session.execute(
            select(Application).where(
                Application.vacancy_uuid == vacancy_uuid, Application.user_uuid == user_uuid
            )
        )
        return result.scalar_one_or_none()

    async def timeline(self, application_uuid: UUID) -> list[ApplicationEvent]:
        result = await self.session.execute(
            select(ApplicationEvent)
            .where(ApplicationEvent.application_uuid == application_uuid)
            .order_by(ApplicationEvent.application_event_uuid)
        )
        return list(result.scalars())

    async def list_my(self, user_uuid: UUID) -> list[tuple[Application, Vacancy, Company]]:
        result = await self.session.execute(
            select(Application, Vacancy, Company)
            .join(Vacancy, Vacancy.vacancy_uuid == Application.vacancy_uuid)
            .join(Company, Company.company_uuid == Vacancy.company_uuid)
            .where(Application.user_uuid == user_uuid, Application.archived_at.is_(None))
            .order_by(Application.application_uuid.desc())
        )
        return [tuple(row) for row in result.all()]

    async def list_for_vacancy(self, vacancy_uuid: UUID) -> list[tuple[Application, User, Vacancy]]:
        result = await self.session.execute(
            select(Application, User, Vacancy)
            .join(User, User.user_uuid == Application.user_uuid)
            .join(Vacancy, Vacancy.vacancy_uuid == Application.vacancy_uuid)
            .where(
                Application.vacancy_uuid == vacancy_uuid,
                Application.archived_at.is_(None),
                _not_blacklisted(Vacancy.company_uuid),
            )
            .order_by(Application.application_uuid.desc())
        )
        return [tuple(row) for row in result.all()]

    async def list_for_company(self, company_uuid: UUID) -> list[tuple[Application, User, Vacancy]]:
        result = await self.session.execute(
            select(Application, User, Vacancy)
            .join(User, User.user_uuid == Application.user_uuid)
            .join(Vacancy, Vacancy.vacancy_uuid == Application.vacancy_uuid)
            .where(
                Vacancy.company_uuid == company_uuid,
                Application.archived_at.is_(None),
                _not_blacklisted(Vacancy.company_uuid),
            )
            .order_by(Application.application_uuid.desc())
        )
        return [tuple(row) for row in result.all()]

    async def is_blacklisted(self, company_uuid: UUID, user_uuid: UUID) -> bool:
        result = await self.session.execute(
            select(CandidateListEntry.entry_uuid).where(
                CandidateListEntry.company_uuid == company_uuid,
                CandidateListEntry.user_uuid == user_uuid,
                CandidateListEntry.list == CandidateList.blacklist,
            )
        )
        return result.scalar_one_or_none() is not None

    async def count_confirmed(self, vacancy_uuid: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Application)
            .where(
                Application.vacancy_uuid == vacancy_uuid,
                Application.status == ApplicationStatus.confirmed,
            )
        )
        return result.scalar_one()

    async def list_confirmed_for_update(self, vacancy_uuid: UUID) -> list[Application]:
        """Подтверждённые заявки смены под блокировкой — для проведения выплаты."""
        result = await self.session.execute(
            select(Application)
            .where(
                Application.vacancy_uuid == vacancy_uuid,
                Application.status == ApplicationStatus.confirmed,
            )
            .with_for_update()
        )
        return list(result.scalars())
