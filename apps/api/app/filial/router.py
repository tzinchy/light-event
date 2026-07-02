from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.filial.schemas import FilialCreateIn, FilialOut, FilialUpdateIn
from app.filial.service import FilialService
from app.user.models import User

router = APIRouter(prefix="/api/v1", tags=["filials"])


def get_filial_service(session: AsyncSession = Depends(get_session)) -> FilialService:
    return FilialService(session=session)


@router.post("/companies/{company_uuid}/filials", response_model=FilialOut, status_code=201)
async def create_filial(
    company_uuid: UUID,
    payload: FilialCreateIn,
    user: User = Depends(get_current_user),
    service: FilialService = Depends(get_filial_service),
) -> FilialOut:
    return FilialOut.model_validate(await service.create(user, company_uuid, payload))


@router.get("/companies/{company_uuid}/filials", response_model=list[FilialOut])
async def list_filials(
    company_uuid: UUID,
    user: User = Depends(get_current_user),
    service: FilialService = Depends(get_filial_service),
) -> list[FilialOut]:
    return [FilialOut.model_validate(f) for f in await service.list_for_member(user, company_uuid)]


@router.patch("/filials/{filial_uuid}", response_model=FilialOut)
async def update_filial(
    filial_uuid: UUID,
    payload: FilialUpdateIn,
    user: User = Depends(get_current_user),
    service: FilialService = Depends(get_filial_service),
) -> FilialOut:
    return FilialOut.model_validate(await service.update(user, filial_uuid, payload))


@router.delete("/filials/{filial_uuid}", status_code=204)
async def delete_filial(
    filial_uuid: UUID,
    user: User = Depends(get_current_user),
    service: FilialService = Depends(get_filial_service),
) -> None:
    await service.delete(user, filial_uuid)
