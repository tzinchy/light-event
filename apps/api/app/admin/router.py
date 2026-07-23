from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import (
    AdminUserCreateIn,
    AdminUserDetailOut,
    AdminUserOut,
    CompanyModerationOut,
    CompanyRejectIn,
    ModerationReasonIn,
    ModerationRequestOut,
    OverviewOut,
    UserRoleUpdateIn,
)
from app.admin.service import AdminCompanyService, AdminOverviewService, AdminQueueService, AdminUserService
from app.company.models import CompanyStatus
from app.core.deps import get_session
from app.core.permissions import require_admin
from app.user.models import ModerationStatus, User

router = APIRouter(
    prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin())]
)


def get_admin_company_service(session: AsyncSession = Depends(get_session)) -> AdminCompanyService:
    return AdminCompanyService(session=session)


@router.get("/overview", response_model=OverviewOut)
async def overview(session: AsyncSession = Depends(get_session)) -> OverviewOut:
    return await AdminOverviewService(session).overview()


@router.get("/requests", response_model=list[ModerationRequestOut])
async def list_requests(
    session: AsyncSession = Depends(get_session),
) -> list[ModerationRequestOut]:
    return await AdminQueueService(session).list_requests()


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


def get_admin_user_service(session: AsyncSession = Depends(get_session)) -> AdminUserService:
    return AdminUserService(session=session)


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    status: ModerationStatus | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    service: AdminUserService = Depends(get_admin_user_service),
) -> list[AdminUserOut]:
    return await service.list_users(status=status, query=q, limit=limit, offset=offset)


@router.post("/users", response_model=AdminUserOut, status_code=201)
async def create_user(
    payload: AdminUserCreateIn,
    service: AdminUserService = Depends(get_admin_user_service),
) -> AdminUserOut:
    return await service.create(email=payload.email, platform_role=payload.platform_role)


@router.get("/users/{user_uuid}", response_model=AdminUserDetailOut)
async def user_detail(
    user_uuid: UUID,
    service: AdminUserService = Depends(get_admin_user_service),
) -> AdminUserDetailOut:
    return await service.detail(user_uuid)


@router.patch("/users/{user_uuid}", response_model=AdminUserOut)
async def update_user(
    user_uuid: UUID,
    payload: UserRoleUpdateIn,
    admin: User = Depends(require_admin()),
    service: AdminUserService = Depends(get_admin_user_service),
) -> AdminUserOut:
    return await service.update(admin, user_uuid, platform_role=payload.platform_role, name=payload.name)


@router.post("/users/{user_uuid}/approve", response_model=AdminUserOut)
async def approve_user(
    user_uuid: UUID,
    admin: User = Depends(require_admin()),
    service: AdminUserService = Depends(get_admin_user_service),
) -> AdminUserOut:
    return await service.approve(admin, user_uuid)


@router.post("/users/{user_uuid}/resubmit", response_model=AdminUserOut)
async def resubmit_user(
    user_uuid: UUID,
    payload: ModerationReasonIn,
    admin: User = Depends(require_admin()),
    service: AdminUserService = Depends(get_admin_user_service),
) -> AdminUserOut:
    return await service.resubmit(admin, user_uuid, payload.reason)


@router.post("/users/{user_uuid}/ban", response_model=AdminUserOut)
async def ban_user(
    user_uuid: UUID,
    payload: ModerationReasonIn,
    admin: User = Depends(require_admin()),
    service: AdminUserService = Depends(get_admin_user_service),
) -> AdminUserOut:
    return await service.ban(admin, user_uuid, payload.reason)


@router.post("/users/{user_uuid}/unban", response_model=AdminUserOut)
async def unban_user(
    user_uuid: UUID,
    admin: User = Depends(require_admin()),
    service: AdminUserService = Depends(get_admin_user_service),
) -> AdminUserOut:
    return await service.unban(admin, user_uuid)
