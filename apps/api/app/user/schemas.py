from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    desired_roles: list[str] | None = None


class EmailRequestIn(BaseModel):
    email: EmailStr = Field(max_length=254)


class EmailConfirmIn(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    user_uuid: UUID
    phone: str | None
    email: str | None
    email_verified_at: datetime | None
    name: str | None
    city: str | None
    platform_role: str
    desired_roles: list[str]
    pd_consent_at: datetime | None
