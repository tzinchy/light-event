from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
    status: str
    reject_reason: str | None
    verified_at: datetime | None
    created_at: datetime


class CompanyRejectIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
