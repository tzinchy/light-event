from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.core.permissions import require_admin
from app.pricing.schemas import PriceOut, PriceUpdateIn
from app.pricing.service import PricingService

router = APIRouter(prefix="/api/v1/admin/pricing", tags=["pricing"], dependencies=[Depends(require_admin())])


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
