from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.vacancy.schemas import VacancyOut


class ApplicationOut(BaseModel):
    model_config = {"from_attributes": True}

    application_uuid: UUID
    vacancy_uuid: UUID
    user_uuid: UUID
    status: str
    created_at: datetime


class TimelineEventOut(BaseModel):
    model_config = {"from_attributes": True}

    kind: str
    occurred_at: datetime


class ApplicationDetailOut(ApplicationOut):
    timeline: list[TimelineEventOut]


class MyApplicationOut(ApplicationOut):
    """Карточка «Мои заявки»: заявка + смена + компания."""

    vacancy: VacancyOut
    company_name: str


class CompanyApplicationOut(ApplicationOut):
    """Строка отклика для компании: заявка + профиль кандидата (без KYC-контента)."""

    user_name: str | None
    vacancy: VacancyOut
    company_test_passed: bool = False


class StatusChangeIn(BaseModel):
    action: Literal["confirm", "reserve"]
