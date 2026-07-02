from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.company.schemas import CompanyCreateIn, CompanyOut, CompanyUpdateIn, MyCompanyOut
from app.company.service import CompanyService
from app.core.deps import get_current_user, get_session
from app.core.permissions import require_member
from app.team.schemas import TeamMemberOut
from app.user.models import User

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def get_company_service(session: AsyncSession = Depends(get_session)) -> CompanyService:
    return CompanyService(session=session)


@router.post("", response_model=CompanyOut, status_code=201)
async def create_company(
    payload: CompanyCreateIn,
    user: User = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
) -> CompanyOut:
    return CompanyOut.model_validate(await service.create(user, payload))


# объявлен до /{company_uuid}, иначе «my» попадает в UUID-парсер
@router.get("/my", response_model=list[MyCompanyOut])
async def my_companies(
    user: User = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
) -> list[MyCompanyOut]:
    return [
        MyCompanyOut(company=CompanyOut.model_validate(company), company_role=member.company_role)
        for company, member in await service.list_my(user)
    ]


@router.get("/{company_uuid}", response_model=CompanyOut)
async def get_company(company_uuid: UUID, service: CompanyService = Depends(get_company_service)) -> CompanyOut:
    return CompanyOut.model_validate(await service.get(company_uuid))


@router.patch("/{company_uuid}", response_model=CompanyOut)
async def update_company(
    company_uuid: UUID,
    payload: CompanyUpdateIn,
    user: User = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
) -> CompanyOut:
    return CompanyOut.model_validate(await service.update(user, company_uuid, payload))


@router.get("/{company_uuid}/team", response_model=list[TeamMemberOut], dependencies=[Depends(require_member())])
async def list_team(
    company_uuid: UUID,
    service: CompanyService = Depends(get_company_service),
) -> list[TeamMemberOut]:
    return [TeamMemberOut.model_validate(m) for m in await service.list_team(company_uuid)]
