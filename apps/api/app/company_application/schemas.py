from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.company.schemas import CompanyCreateIn


class ApplicationSubmitIn(CompanyCreateIn):
    """Данные заявки совпадают с созданием компании (валидаторы ИНН/ОГРН переиспользуются)."""


class ApplicationSubmitOut(BaseModel):
    company_application_uuid: UUID
    status: str
    upload_token: str  # отдаётся один раз — для догрузки пруф-документа


class AdminApplicationOut(BaseModel):
    model_config = {"from_attributes": True}

    company_application_uuid: UUID
    name: str
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
    company_uuid: UUID | None
    has_document: bool = False
    created_at: datetime


class ApplicationApproveOut(BaseModel):
    company_application_uuid: UUID
    status: str
    company_uuid: UUID


class ApplicationRejectIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
