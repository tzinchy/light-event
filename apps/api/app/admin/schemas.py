from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CompanyModerationOut(BaseModel):
    """Карточка заявки для админа — с реквизитами, которые не отдаются наружу."""

    model_config = {"from_attributes": True}

    company_uuid: UUID
    name: str
    description: str | None
    inn: str
    ogrn: str
    address: str
    lat: float
    lon: float
    contact_phone: str
    contact_name: str
    contact_email: str
    contact_position: str
    status: str
    reject_reason: str | None
    verified_at: datetime | None
    created_at: datetime


class CompanyRejectIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ModerationRequestOut(BaseModel):
    """Элемент единой очереди модерации: платная публикация смены или теста компании."""

    kind: str  # vacancy | test
    ref_uuid: UUID
    title: str
    company_uuid: UUID | None
    company_name: str | None
    submitted_at: datetime


class AdminUserOut(BaseModel):
    """Строка списка пользователей в админке (PLAN §11.15)."""

    model_config = {"from_attributes": True}

    user_uuid: UUID
    email: str | None
    phone: str | None
    name: str | None
    platform_role: str
    moderation_status: str
    moderation_reason: str | None
    is_active: bool
    documents_count: int = 0
    created_at: datetime


class AdminUserDocumentOut(BaseModel):
    model_config = {"from_attributes": True}

    document_uuid: UUID
    kind: str
    status: str
    reject_reason: str | None
    created_at: datetime


class AdminUserDetailOut(AdminUserOut):
    documents: list[AdminUserDocumentOut] = []


class UserRoleUpdateIn(BaseModel):
    platform_role: str | None = None
    name: str | None = Field(default=None, max_length=120)


class ModerationReasonIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class AdminUserCreateIn(BaseModel):
    email: EmailStr = Field(max_length=254)
    platform_role: str = "user"


class OverviewOut(BaseModel):
    """Сводка админа: 4 стата референса + счётчики очередей модерации."""

    users_count: int
    kyc_verified_pct: float
    turnover_kop: int
    open_complaints: int
    queues: dict[str, int]
