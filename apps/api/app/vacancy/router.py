from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.core.permissions import require_admin
from app.user.models import User
from app.vacancy.schemas import FeedItemOut, ModerateIn, VacancyCreateIn, VacancyOut, VacancyUpdateIn
from app.vacancy.service import VacancyService

router = APIRouter(prefix="/api/v1", tags=["vacancies"])


def get_vacancy_service(request: Request, session: AsyncSession = Depends(get_session)) -> VacancyService:
    return VacancyService(session=session, settings=request.app.state.settings)


@router.get("/vacancies", response_model=list[FeedItemOut])
async def feed(
    role: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    company_uuid: UUID | None = None,
    service: VacancyService = Depends(get_vacancy_service),
) -> list[FeedItemOut]:
    rows = await service.feed(role=role, date_from=date_from, date_to=date_to, company_uuid=company_uuid)
    return [
        FeedItemOut(
            **VacancyOut.model_validate(vacancy).model_dump(), company_name=company.name, filled=filled
        )
        for vacancy, company, filled in rows
    ]


@router.get("/vacancies/{vacancy_uuid}", response_model=VacancyOut)
async def vacancy_detail(
    vacancy_uuid: UUID, service: VacancyService = Depends(get_vacancy_service)
) -> VacancyOut:
    return VacancyOut.model_validate(await service.get(vacancy_uuid))


@router.post("/companies/{company_uuid}/vacancies", response_model=VacancyOut, status_code=201)
async def create_vacancy(
    company_uuid: UUID,
    payload: VacancyCreateIn,
    user: User = Depends(get_current_user),
    service: VacancyService = Depends(get_vacancy_service),
) -> VacancyOut:
    return VacancyOut.model_validate(await service.create(user, company_uuid, payload))


@router.get("/companies/{company_uuid}/vacancies", response_model=list[VacancyOut])
async def company_vacancies(
    company_uuid: UUID,
    user: User = Depends(get_current_user),
    service: VacancyService = Depends(get_vacancy_service),
) -> list[VacancyOut]:
    return [VacancyOut.model_validate(v) for v in await service.list_by_company(user, company_uuid)]


@router.patch("/vacancies/{vacancy_uuid}", response_model=VacancyOut)
async def update_vacancy(
    vacancy_uuid: UUID,
    payload: VacancyUpdateIn,
    user: User = Depends(get_current_user),
    service: VacancyService = Depends(get_vacancy_service),
) -> VacancyOut:
    return VacancyOut.model_validate(await service.update(user, vacancy_uuid, payload))


@router.post("/vacancies/{vacancy_uuid}/publish", response_model=VacancyOut)
async def publish_vacancy(
    vacancy_uuid: UUID,
    user: User = Depends(get_current_user),
    service: VacancyService = Depends(get_vacancy_service),
) -> VacancyOut:
    return VacancyOut.model_validate(await service.publish(user, vacancy_uuid))


@router.post("/vacancies/{vacancy_uuid}/archive", response_model=VacancyOut)
async def archive_vacancy(
    vacancy_uuid: UUID,
    user: User = Depends(get_current_user),
    service: VacancyService = Depends(get_vacancy_service),
) -> VacancyOut:
    return VacancyOut.model_validate(await service.archive(user, vacancy_uuid))


@router.post("/admin/vacancies/{vacancy_uuid}/moderate", response_model=VacancyOut)
async def moderate_vacancy(
    vacancy_uuid: UUID,
    payload: ModerateIn,
    admin: User = Depends(require_admin()),
    service: VacancyService = Depends(get_vacancy_service),
) -> VacancyOut:
    return VacancyOut.model_validate(await service.moderate(admin, vacancy_uuid, payload))
