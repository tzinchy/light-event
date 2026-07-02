from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.candidate_list.schemas import CandidateEntryIn, CandidateEntryOut
from app.candidate_list.service import CandidateListService
from app.core.deps import get_current_user, get_session
from app.user.models import User

router = APIRouter(prefix="/api/v1/companies/{company_uuid}/candidates", tags=["candidates"])


def get_candidate_service(session: AsyncSession = Depends(get_session)) -> CandidateListService:
    return CandidateListService(session=session)


@router.get("", response_model=list[CandidateEntryOut])
async def list_candidates(
    company_uuid: UUID,
    list: Literal["shortlist", "reserve", "blacklist"] | None = None,
    user: User = Depends(get_current_user),
    service: CandidateListService = Depends(get_candidate_service),
) -> list[CandidateEntryOut]:
    return [CandidateEntryOut.model_validate(e) for e in await service.list(user, company_uuid, list)]


@router.put("/{user_uuid}", response_model=CandidateEntryOut)
async def put_candidate(
    company_uuid: UUID,
    user_uuid: UUID,
    payload: CandidateEntryIn,
    user: User = Depends(get_current_user),
    service: CandidateListService = Depends(get_candidate_service),
) -> CandidateEntryOut:
    return CandidateEntryOut.model_validate(await service.put(user, company_uuid, user_uuid, payload))


@router.delete("/{user_uuid}", status_code=204)
async def delete_candidate(
    company_uuid: UUID,
    user_uuid: UUID,
    user: User = Depends(get_current_user),
    service: CandidateListService = Depends(get_candidate_service),
) -> None:
    await service.delete(user, company_uuid, user_uuid)
