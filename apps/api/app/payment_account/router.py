from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.core.permissions import require_admin
from app.payment_account.schemas import PaymentAccountCreateIn, PaymentAccountOut, PaymentAccountUpdateIn
from app.payment_account.service import PaymentAccountService

router = APIRouter(
    prefix="/api/v1/admin/payment-accounts", tags=["payment_account"], dependencies=[Depends(require_admin())]
)


def get_service(session: AsyncSession = Depends(get_session)) -> PaymentAccountService:
    return PaymentAccountService(session=session)


@router.get("", response_model=list[PaymentAccountOut])
async def list_accounts(service: PaymentAccountService = Depends(get_service)) -> list[PaymentAccountOut]:
    return await service.list_with_usage()


@router.post("", response_model=PaymentAccountOut, status_code=201)
async def create_account(
    payload: PaymentAccountCreateIn, service: PaymentAccountService = Depends(get_service)
) -> PaymentAccountOut:
    return PaymentAccountOut.model_validate(await service.create(payload))


@router.patch("/{payment_account_uuid}", response_model=PaymentAccountOut)
async def update_account(
    payment_account_uuid: UUID,
    payload: PaymentAccountUpdateIn,
    service: PaymentAccountService = Depends(get_service),
) -> PaymentAccountOut:
    return PaymentAccountOut.model_validate(await service.update(payment_account_uuid, payload))


@router.post("/{payment_account_uuid}/priority", response_model=PaymentAccountOut)
async def set_priority(
    payment_account_uuid: UUID, service: PaymentAccountService = Depends(get_service)
) -> PaymentAccountOut:
    return PaymentAccountOut.model_validate(await service.set_priority(payment_account_uuid))
