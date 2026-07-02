from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.models import Application, ApplicationEvent, ApplicationEventKind, ApplicationStatus
from app.application.repo import ApplicationRepo
from app.application.schemas import StatusChangeIn
from app.core.errors import DomainError
from app.core.permissions import ensure_permission
from app.team.repo import TeamRepo
from app.user.models import User
from app.vacancy.models import VacancyStatus
from app.vacancy.repo import VacancyRepo


class ApplicationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.applications = ApplicationRepo(session)
        self.vacancies = VacancyRepo(session)

    async def apply(self, actor: User, vacancy_uuid: UUID) -> Application:
        vacancy = await self.vacancies.get(vacancy_uuid)
        if vacancy is None:
            raise DomainError(404, "Смена не найдена")
        if vacancy.status != VacancyStatus.active or vacancy.archived_at is not None:
            raise DomainError(409, "Смена не открыта для откликов")
        if await self.applications.get_by_vacancy_user(vacancy_uuid, actor.user_uuid) is not None:
            raise DomainError(409, "Вы уже откликнулись на эту смену")
        application = Application(vacancy_uuid=vacancy_uuid, user_uuid=actor.user_uuid)
        self.applications.add(application)
        await self.session.flush()
        self.applications.add_event(
            ApplicationEvent(
                application_uuid=application.application_uuid,
                kind=ApplicationEventKind.applied,
                actor_uuid=actor.user_uuid,
            )
        )
        await self.session.flush()
        return application

    async def list_my(self, actor: User):
        return await self.applications.list_my(actor.user_uuid)

    async def get_detail(self, actor: User, application_uuid: UUID):
        application = await self.applications.get(application_uuid)
        if application is None:
            raise DomainError(404, "Заявка не найдена")
        if application.user_uuid != actor.user_uuid:
            # доступ команде компании с правом hire
            vacancy = await self.vacancies.get(application.vacancy_uuid)
            member = await TeamRepo(self.session).get_membership(actor.user_uuid, vacancy.company_uuid)
            if member is None or not member.has_permission("hire"):
                raise DomainError(403, "Нет доступа к этой заявке")
        timeline = await self.applications.timeline(application_uuid)
        return application, timeline

    async def set_status(self, actor: User, application_uuid: UUID, data: StatusChangeIn) -> Application:
        application = await self.applications.get_for_update(application_uuid)
        if application is None:
            raise DomainError(404, "Заявка не найдена")
        vacancy = await self.vacancies.get(application.vacancy_uuid)
        await ensure_permission(self.session, actor, vacancy.company_uuid, "hire")
        # кандидат из ЧС для компании не существует (skill rbac-permissions)
        if await self.applications.is_blacklisted(vacancy.company_uuid, application.user_uuid):
            raise DomainError(404, "Заявка не найдена")
        if application.status not in (ApplicationStatus.review, ApplicationStatus.reserve, ApplicationStatus.confirmed):
            raise DomainError(409, "Статус заявки уже не меняется")
        if data.action == "confirm":
            if application.status == ApplicationStatus.confirmed:
                raise DomainError(409, "Заявка уже подтверждена")
            if await self.applications.count_confirmed(vacancy.vacancy_uuid) >= vacancy.slots:
                raise DomainError(409, "Все места уже набраны")
            application.status = ApplicationStatus.confirmed
            self.applications.add_event(
                ApplicationEvent(
                    application_uuid=application.application_uuid,
                    kind=ApplicationEventKind.confirmed,
                    actor_uuid=actor.user_uuid,
                )
            )
        else:
            application.status = ApplicationStatus.reserve
        await self.session.flush()
        return application

    async def list_for_vacancy(self, actor: User, vacancy_uuid: UUID):
        vacancy = await self.vacancies.get(vacancy_uuid)
        if vacancy is None:
            raise DomainError(404, "Смена не найдена")
        await ensure_permission(self.session, actor, vacancy.company_uuid, "hire")
        return await self.applications.list_for_vacancy(vacancy_uuid)

    async def list_for_company(self, actor: User, company_uuid: UUID):
        await ensure_permission(self.session, actor, company_uuid, "hire")
        return await self.applications.list_for_company(company_uuid)
