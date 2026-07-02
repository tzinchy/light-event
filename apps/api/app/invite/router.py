from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.invite.schemas import InviteCreateIn, InviteOut
from app.invite.service import InviteService
from app.team.schemas import TeamMemberOut
from app.user.models import User

router = APIRouter(prefix="/api/v1", tags=["invites"])


def get_invite_service(session: AsyncSession = Depends(get_session)) -> InviteService:
    return InviteService(session=session)


@router.post("/companies/{company_uuid}/invites", response_model=InviteOut, status_code=201)
async def create_invite(
    company_uuid: UUID,
    payload: InviteCreateIn,
    user: User = Depends(get_current_user),
    service: InviteService = Depends(get_invite_service),
) -> InviteOut:
    return InviteOut.model_validate(await service.create(user, company_uuid, payload))


@router.get("/companies/{company_uuid}/invites", response_model=list[InviteOut])
async def list_invites(
    company_uuid: UUID,
    user: User = Depends(get_current_user),
    service: InviteService = Depends(get_invite_service),
) -> list[InviteOut]:
    return [InviteOut.model_validate(i) for i in await service.list_for_company(user, company_uuid)]


@router.post("/invites/{code}/accept", response_model=TeamMemberOut, status_code=201)
async def accept_invite(
    code: str,
    user: User = Depends(get_current_user),
    service: InviteService = Depends(get_invite_service),
) -> TeamMemberOut:
    return TeamMemberOut.model_validate(await service.accept(user, code))


@router.post("/invites/{invite_link_uuid}/revoke", response_model=InviteOut)
async def revoke_invite(
    invite_link_uuid: UUID,
    user: User = Depends(get_current_user),
    service: InviteService = Depends(get_invite_service),
) -> InviteOut:
    return InviteOut.model_validate(await service.revoke(user, invite_link_uuid))
