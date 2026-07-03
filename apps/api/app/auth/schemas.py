from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

PHONE_PATTERN = r"^\+\d{10,15}$"


class OtpRequestIn(BaseModel):
    phone: str = Field(pattern=PHONE_PATTERN)


class OtpVerifyIn(BaseModel):
    phone: str = Field(pattern=PHONE_PATTERN)
    code: str = Field(min_length=6, max_length=6)


class RefreshIn(BaseModel):
    refresh_token: str


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


class MeOut(BaseModel):
    model_config = {"from_attributes": True}

    user_uuid: UUID
    phone: str
    email: str | None
    email_verified_at: datetime | None
    name: str | None
    city: str | None
    platform_role: str
    pd_consent_at: datetime | None
