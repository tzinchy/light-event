from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.balance.schemas import AccountOut, OperationOut, TopupCreateIn, TopupRequestOut, TopupResolveIn
from app.balance.service import BalanceService
from app.core.deps import get_current_user, get_session
from app.core.permissions import require_admin
from app.user.models import User

router = APIRouter(prefix="/api/v1", tags=["balance"])


def get_balance_service(session: AsyncSession = Depends(get_session)) -> BalanceService:
    return BalanceService(session=session)


@router.get("/companies/{company_uuid}/account", response_model=AccountOut)
async def company_account(
    company_uuid: UUID,
    user: User = Depends(get_current_user),
    service: BalanceService = Depends(get_balance_service),
) -> AccountOut:
    return AccountOut.model_validate(await service.get_company_account(user, company_uuid))


@router.get("/companies/{company_uuid}/account/operations", response_model=list[OperationOut])
async def company_operations(
    company_uuid: UUID,
    user: User = Depends(get_current_user),
    service: BalanceService = Depends(get_balance_service),
) -> list[OperationOut]:
    return await service.list_company_operations(user, company_uuid)


@router.post("/companies/{company_uuid}/topup-requests", response_model=TopupRequestOut, status_code=201)
async def create_topup_request(
    company_uuid: UUID,
    payload: TopupCreateIn,
    user: User = Depends(get_current_user),
    service: BalanceService = Depends(get_balance_service),
) -> TopupRequestOut:
    return TopupRequestOut.model_validate(await service.create_topup_request(user, company_uuid, payload))


@router.get(
    "/admin/topup-requests", response_model=list[TopupRequestOut], dependencies=[Depends(require_admin())]
)
async def admin_list_topup_requests(
    service: BalanceService = Depends(get_balance_service),
) -> list[TopupRequestOut]:
    return [TopupRequestOut.model_validate(t) for t in await service.list_topup_requests()]


@router.post("/admin/topup-requests/{topup_request_uuid}/resolve", response_model=TopupRequestOut)
async def admin_resolve_topup(
    topup_request_uuid: UUID,
    payload: TopupResolveIn,
    admin: User = Depends(require_admin()),
    service: BalanceService = Depends(get_balance_service),
) -> TopupRequestOut:
    return TopupRequestOut.model_validate(await service.resolve_topup(admin, topup_request_uuid, payload))
