from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class VacancyCreateIn(BaseModel):
    filial_uuid: UUID
    role_name: str = Field(min_length=2, max_length=80)
    event_title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    starts_at: datetime
    ends_at: datetime
    venue_address: str = Field(min_length=2, max_length=300)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    pay_hour_kop: int = Field(ge=1)
    slots: int = Field(ge=1, le=500)
    urgent: bool = False
    tags: list[str] = Field(default_factory=list, max_length=10)
    requirements: list[str] = Field(default_factory=list, max_length=20)
    required_test_uuids: list[UUID] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def ends_after_starts(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("Окончание смены должно быть позже начала")
        return self


class VacancyUpdateIn(BaseModel):
    role_name: str | None = Field(default=None, min_length=2, max_length=80)
    event_title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    venue_address: str | None = Field(default=None, min_length=2, max_length=300)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    pay_hour_kop: int | None = Field(default=None, ge=1)
    slots: int | None = Field(default=None, ge=1, le=500)
    urgent: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=10)
    requirements: list[str] | None = Field(default=None, max_length=20)
    required_test_uuids: list[UUID] | None = Field(default=None, max_length=10)


class VacancyOut(BaseModel):
    model_config = {"from_attributes": True}

    vacancy_uuid: UUID
    company_uuid: UUID
    filial_uuid: UUID
    role_name: str
    event_title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime
    venue_address: str
    lat: float | None
    lon: float | None
    pay_hour_kop: int
    pay_total_kop: int
    slots: int
    urgent: bool
    tags: list[str]
    requirements: list[str]
    required_test_uuids: list[UUID]
    status: str
    reject_reason: str | None
    archived_at: datetime | None
    created_at: datetime


class FeedItemOut(VacancyOut):
    """Карточка ленты: вакансия + витринные поля компании и заполняемость."""

    company_name: str
    company_rating: float | None = None
    filled: int = 0


class ModerateIn(BaseModel):
    action: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=500)
