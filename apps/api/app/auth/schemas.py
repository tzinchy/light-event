from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# используется в других модулях для валидации контактных телефонов (не логин)
PHONE_PATTERN = r"^\+\d{10,15}$"


class OtpRequestIn(BaseModel):
    email: EmailStr = Field(max_length=254)


class OtpVerifyIn(BaseModel):
    email: EmailStr = Field(max_length=254)
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
    phone: str | None
    email: str | None
    email_verified_at: datetime | None
    name: str | None
    city: str | None
    platform_role: str
    experience: str | None = None
    about: str | None = None
    english_level: str | None = None
    education: str | None = None
    pd_consent_at: datetime | None
