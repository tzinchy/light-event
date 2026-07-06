from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.core.permissions import ensure_membership, require_admin
from app.pricing.schemas import PriceOut, PriceUpdateIn
from app.pricing.service import PricingService
from app.user.models import User

router = APIRouter(prefix="/api/v1/admin/pricing", tags=["pricing"], dependencies=[Depends(require_admin())])
# per-company тарифы (§11.10-A): админ управляет, участник компании видит эффективные цены
company_router = APIRouter(prefix="/api/v1", tags=["pricing"])


def get_pricing_service(request: Request, session: AsyncSession = Depends(get_session)) -> PricingService:
    return PricingService(session=session, settings=request.app.state.settings)


@router.get("", response_model=list[PriceOut])
async def list_prices(service: PricingService = Depends(get_pricing_service)) -> list[PriceOut]:
    return [PriceOut(**p) for p in await service.list_prices()]


@router.put("/{key}", response_model=PriceOut)
async def set_price(
    key: str, payload: PriceUpdateIn, service: PricingService = Depends(get_pricing_service)
) -> PriceOut:
    return PriceOut(**await service.set_price(key, payload.amount_kop))


@company_router.get(
    "/admin/companies/{company_uuid}/pricing",
    response_model=list[PriceOut],
    dependencies=[Depends(require_admin())],
)
async def company_prices_admin(
    company_uuid: UUID, service: PricingService = Depends(get_pricing_service)
) -> list[PriceOut]:
    return [PriceOut(**p) for p in await service.list_prices(company_uuid)]


@company_router.put(
    "/admin/companies/{company_uuid}/pricing/{key}",
    response_model=PriceOut,
    dependencies=[Depends(require_admin())],
)
async def set_company_price(
    company_uuid: UUID,
    key: str,
    payload: PriceUpdateIn,
    service: PricingService = Depends(get_pricing_service),
) -> PriceOut:
    return PriceOut(**await service.set_price(key, payload.amount_kop, company_uuid))


@company_router.get("/companies/{company_uuid}/pricing", response_model=list[PriceOut])
async def company_prices(
    company_uuid: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: PricingService = Depends(get_pricing_service),
) -> list[PriceOut]:
    """Эффективные цены для компании — видит её команда (реальные цены на формах)."""
    await ensure_membership(session, user, company_uuid)
    return [PriceOut(**p) for p in await service.list_prices(company_uuid)]
