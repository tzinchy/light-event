from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.company.schemas import CompanyOut
from app.core.deps import get_current_user, get_session
from app.favorite.service import FavoriteService
from app.user.models import User

router = APIRouter(prefix="/api/v1", tags=["favorite"])


def get_favorite_service(session: AsyncSession = Depends(get_session)) -> FavoriteService:
    return FavoriteService(session=session)


@router.post("/companies/{company_uuid}/favorite", status_code=201)
async def follow(
    company_uuid: UUID,
    actor: User = Depends(get_current_user),
    service: FavoriteService = Depends(get_favorite_service),
) -> dict:
    await service.follow(actor, company_uuid)
    return {"ok": True}


@router.delete("/companies/{company_uuid}/favorite", status_code=204)
async def unfollow(
    company_uuid: UUID,
    actor: User = Depends(get_current_user),
    service: FavoriteService = Depends(get_favorite_service),
) -> None:
    await service.unfollow(actor, company_uuid)


@router.get("/favorites/companies", response_model=list[CompanyOut])
async def my_favorites(
    actor: User = Depends(get_current_user),
    service: FavoriteService = Depends(get_favorite_service),
) -> list[CompanyOut]:
    return await service.list_companies(actor)
