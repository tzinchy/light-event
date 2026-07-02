from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.team.schemas import TeamMemberOut, TeamPermissionsPatchIn
from app.team.service import TeamService
from app.user.models import User

router = APIRouter(prefix="/api/v1/team-members", tags=["team"])


def get_team_service(session: AsyncSession = Depends(get_session)) -> TeamService:
    return TeamService(session=session)


@router.patch("/{team_member_uuid}/permissions", response_model=TeamMemberOut)
async def update_permissions(
    team_member_uuid: UUID,
    payload: TeamPermissionsPatchIn,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> TeamMemberOut:
    return TeamMemberOut.model_validate(await service.update_permissions(user, team_member_uuid, payload))


@router.delete("/{team_member_uuid}", status_code=204)
async def remove_member(
    team_member_uuid: UUID,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> None:
    await service.remove_member(user, team_member_uuid)
