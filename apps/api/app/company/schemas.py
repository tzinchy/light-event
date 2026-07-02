from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class CompanyUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class CompanyOut(BaseModel):
    model_config = {"from_attributes": True}

    company_uuid: UUID
    name: str
    description: str | None
    status: str
    created_at: datetime


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
