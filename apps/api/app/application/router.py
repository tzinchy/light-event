from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas import (
    ApplicationDetailOut,
    ApplicationOut,
    CompanyApplicationOut,
    MyApplicationOut,
    StatusChangeIn,
    TimelineEventOut,
)
from app.application.service import ApplicationService
from app.core.deps import get_current_user, get_session
from app.user.models import User
from app.vacancy.schemas import VacancyOut

router = APIRouter(prefix="/api/v1", tags=["applications"])


def get_application_service(session: AsyncSession = Depends(get_session)) -> ApplicationService:
    return ApplicationService(session=session)


@router.post("/vacancies/{vacancy_uuid}/applications", response_model=ApplicationOut, status_code=201)
async def apply(
    vacancy_uuid: UUID,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationOut:
    return ApplicationOut.model_validate(await service.apply(user, vacancy_uuid))


@router.get("/applications/my", response_model=list[MyApplicationOut])
async def my_applications(
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
) -> list[MyApplicationOut]:
    rows = await service.list_my(user)
    return [
        MyApplicationOut(
            **ApplicationOut.model_validate(application).model_dump(),
            vacancy=VacancyOut.model_validate(vacancy),
            company_name=company.name,
        )
        for application, vacancy, company in rows
    ]


@router.get("/applications/{application_uuid}", response_model=ApplicationDetailOut)
async def application_detail(
    application_uuid: UUID,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationDetailOut:
    application, timeline = await service.get_detail(user, application_uuid)
    return ApplicationDetailOut(
        **ApplicationOut.model_validate(application).model_dump(),
        timeline=[TimelineEventOut.model_validate(e) for e in timeline],
    )


@router.post("/applications/{application_uuid}/status", response_model=ApplicationOut)
async def change_status(
    application_uuid: UUID,
    payload: StatusChangeIn,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationOut:
    return ApplicationOut.model_validate(await service.set_status(user, application_uuid, payload))


def _company_rows(rows) -> list[CompanyApplicationOut]:
    return [
        CompanyApplicationOut(
            **ApplicationOut.model_validate(application).model_dump(),
            user_name=candidate.name,
            vacancy=VacancyOut.model_validate(vacancy),
        )
        for application, candidate, vacancy in rows
    ]


@router.get("/vacancies/{vacancy_uuid}/applications", response_model=list[CompanyApplicationOut])
async def vacancy_applications(
    vacancy_uuid: UUID,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
) -> list[CompanyApplicationOut]:
    return _company_rows(await service.list_for_vacancy(user, vacancy_uuid))


@router.get("/companies/{company_uuid}/applications", response_model=list[CompanyApplicationOut])
async def company_applications(
    company_uuid: UUID,
    user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
) -> list[CompanyApplicationOut]:
    return _company_rows(await service.list_for_company(user, company_uuid))
