from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

# опыт работы (PLAN §3.1) — метка → отдаётся как есть; лейблы на фронте
EXPERIENCE_VALUES = ("none", "up_to_1y", "y1_3", "y3_6")


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    desired_roles: list[str] | None = None
    experience: str | None = Field(default=None)

    @field_validator("experience")
    @classmethod
    def _exp(cls, v: str | None) -> str | None:
        if v is not None and v not in EXPERIENCE_VALUES:
            raise ValueError(f"experience должен быть одним из {EXPERIENCE_VALUES}")
        return v


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
    experience: str | None
    pd_consent_at: datetime | None


class WorkerPublicOut(BaseModel):
    """Публичный профиль соискателя для организации — БЕЗ контактов (телефон/почта не отдаём)."""

    model_config = {"from_attributes": True}

    user_uuid: UUID
    name: str | None
    city: str | None
    desired_roles: list[str]
    experience: str | None
