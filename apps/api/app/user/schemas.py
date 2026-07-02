from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    desired_roles: list[str] | None = None


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    user_uuid: UUID
    phone: str
    name: str | None
    city: str | None
    platform_role: str
    desired_roles: list[str]
    pd_consent_at: datetime | None
