import re
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

# справочники профиля (PLAN §3.1) — метки; лейблы на фронте
EXPERIENCE_VALUES = ("none", "up_to_1y", "y1_3", "y3_6")
ENGLISH_VALUES = ("none", "basic", "intermediate", "advanced", "fluent")
EDUCATION_VALUES = ("secondary", "vocational", "higher")
GENDER_VALUES = ("male", "female")
TELEGRAM_RE = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    desired_roles: list[str] | None = None
    experience: str | None = Field(default=None)
    about: str | None = Field(default=None, max_length=2000)
    english_level: str | None = Field(default=None)
    education: str | None = Field(default=None)
    telegram: str | None = Field(default=None)
    birth_date: date | None = None
    citizenship: str | None = Field(default=None, max_length=100)
    gender: str | None = Field(default=None)

    @field_validator("telegram")
    @classmethod
    def _tg(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        if not TELEGRAM_RE.match(v):
            raise ValueError("Телеграм-тег: 5–32 символа, латиница/цифры/подчёркивание")
        return v.lstrip("@")

    @field_validator("gender")
    @classmethod
    def _gender(cls, v: str | None) -> str | None:
        if v is not None and v not in GENDER_VALUES:
            raise ValueError(f"gender должен быть одним из {GENDER_VALUES}")
        return v

    @field_validator("birth_date")
    @classmethod
    def _bd(cls, v: date | None) -> date | None:
        if v is not None and (v > date.today() or v.year < 1900):
            raise ValueError("Некорректная дата рождения")
        return v

    @field_validator("experience")
    @classmethod
    def _exp(cls, v: str | None) -> str | None:
        if v is not None and v not in EXPERIENCE_VALUES:
            raise ValueError(f"experience должен быть одним из {EXPERIENCE_VALUES}")
        return v

    @field_validator("english_level")
    @classmethod
    def _eng(cls, v: str | None) -> str | None:
        if v is not None and v not in ENGLISH_VALUES:
            raise ValueError(f"english_level должен быть одним из {ENGLISH_VALUES}")
        return v

    @field_validator("education")
    @classmethod
    def _edu(cls, v: str | None) -> str | None:
        if v is not None and v not in EDUCATION_VALUES:
            raise ValueError(f"education должен быть одним из {EDUCATION_VALUES}")
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
    about: str | None
    english_level: str | None
    education: str | None
    telegram: str | None
    birth_date: date | None
    citizenship: str | None
    gender: str | None
    pd_consent_at: datetime | None


class WorkerPublicOut(BaseModel):
    """Профиль соискателя для организации — БЕЗ контактов (телефон/почта/телеграм не отдаём).

    Виден только админу, самому пользователю и командам компаний, куда он откликнулся (§11.12).
    """

    model_config = {"from_attributes": True}

    user_uuid: UUID
    name: str | None
    city: str | None
    desired_roles: list[str]
    experience: str | None
    about: str | None
    english_level: str | None
    education: str | None
    birth_date: date | None
    citizenship: str | None
    gender: str | None
