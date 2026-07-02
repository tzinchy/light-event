from uuid import UUID

from pydantic import BaseModel


class TeamMemberOut(BaseModel):
    model_config = {"from_attributes": True}

    team_member_uuid: UUID
    user_uuid: UUID
    company_role: str
    filial_uuid: UUID | None
    email: str | None
    perm_create: bool
    perm_hire: bool
    perm_finance: bool
    perm_invite: bool


class TeamPermissionsPatchIn(BaseModel):
    perm_create: bool | None = None
    perm_hire: bool | None = None
    perm_finance: bool | None = None
    perm_invite: bool | None = None
