from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.auth.schemas import PHONE_PATTERN


def _control_digit(digits: str, weights: list[int]) -> int:
    return sum(int(d) * w for d, w in zip(digits, weights)) % 11 % 10


def validate_inn(value: str) -> str:
    if not value.isdigit() or len(value) not in (10, 12):
        raise ValueError("ИНН — 10 или 12 цифр")
    if len(value) == 10:
        if _control_digit(value[:9], [2, 4, 10, 3, 5, 9, 4, 6, 8]) != int(value[9]):
            raise ValueError("Неверная контрольная цифра ИНН")
    else:
        if _control_digit(value[:10], [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) != int(value[10]) or _control_digit(
            value[:11], [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        ) != int(value[11]):
            raise ValueError("Неверная контрольная цифра ИНН")
    return value


def validate_ogrn(value: str) -> str:
    if not value.isdigit() or len(value) not in (13, 15):
        raise ValueError("ОГРН — 13 цифр (или 15 для ИП)")
    if len(value) == 13:
        ok = int(value[:12]) % 11 % 10 == int(value[12])
    else:
        ok = int(value[:14]) % 13 % 10 == int(value[14])
    if not ok:
        raise ValueError("Неверная контрольная цифра ОГРН")
    return value


class CompanyCreateIn(BaseModel):
    """Заявка на регистрацию организации — уходит на модерацию админу (PLAN §10.4)."""

    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    inn: str
    ogrn: str
    address: str = Field(min_length=5, max_length=300)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    contact_phone: str = Field(pattern=PHONE_PATTERN)
    contact_name: str = Field(min_length=2, max_length=200)
    contact_email: EmailStr = Field(max_length=254)
    contact_position: str = Field(min_length=2, max_length=120)

    _inn = field_validator("inn")(validate_inn)
    _ogrn = field_validator("ogrn")(validate_ogrn)


class CompanyUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class CompanyOut(BaseModel):
    model_config = {"from_attributes": True}

    company_uuid: UUID
    name: str
    description: str | None
    address: str
    lat: float
    lon: float
    status: str
    reject_reason: str | None
    verified_at: datetime | None
    created_at: datetime


class MyCompanyOut(BaseModel):
    company: CompanyOut
    company_role: str
