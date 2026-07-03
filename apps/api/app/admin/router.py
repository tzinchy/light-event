from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import CompanyModerationOut, CompanyRejectIn
from app.admin.service import AdminCompanyService
from app.company.models import CompanyStatus
from app.core.deps import get_session
from app.core.permissions import require_admin

router = APIRouter(
    prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin())]
)


def get_admin_company_service(session: AsyncSession = Depends(get_session)) -> AdminCompanyService:
    return AdminCompanyService(session=session)


@router.get("/companies", response_model=list[CompanyModerationOut])
async def list_companies(
    status: CompanyStatus = CompanyStatus.pending,
    service: AdminCompanyService = Depends(get_admin_company_service),
) -> list[CompanyModerationOut]:
    return [CompanyModerationOut.model_validate(c) for c in await service.list_by_status(status)]


@router.post("/companies/{company_uuid}/verify", response_model=CompanyModerationOut)
async def verify_company(
    company_uuid: UUID,
    service: AdminCompanyService = Depends(get_admin_company_service),
) -> CompanyModerationOut:
    return CompanyModerationOut.model_validate(await service.verify(company_uuid))


@router.post("/companies/{company_uuid}/reject", response_model=CompanyModerationOut)
async def reject_company(
    company_uuid: UUID,
    payload: CompanyRejectIn,
    service: AdminCompanyService = Depends(get_admin_company_service),
) -> CompanyModerationOut:
    return CompanyModerationOut.model_validate(await service.reject(company_uuid, payload.reason))
