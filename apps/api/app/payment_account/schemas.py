from uuid import UUID

from pydantic import BaseModel, Field


class PaymentAccountCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    requisites: str = Field(min_length=2, max_length=1000)
    monthly_limit_kop: int = Field(ge=1)
    is_priority: bool = False


class PaymentAccountUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    requisites: str | None = Field(default=None, min_length=2, max_length=1000)
    monthly_limit_kop: int | None = Field(default=None, ge=1)
    active: bool | None = None


class PaymentAccountOut(BaseModel):
    model_config = {"from_attributes": True}

    payment_account_uuid: UUID
    name: str
    requisites: str
    monthly_limit_kop: int
    is_priority: bool
    active: bool
    received_this_month_kop: int = 0
