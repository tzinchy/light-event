from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AccountOut(BaseModel):
    model_config = {"from_attributes": True}

    account_uuid: UUID
    available_kop: int
    on_hold_kop: int
    total_kop: int


class OperationOut(BaseModel):
    ledger_entry_uuid: UUID
    kind: str
    amount_kop: int
    direction: Literal["in", "out"]  # относительно счёта, по которому запрошены операции
    comment: str | None
    created_at: datetime


class TopupCreateIn(BaseModel):
    amount_kop: int = Field(ge=1)
    proof_document_uuid: UUID
    payment_details: str | None = Field(default=None, max_length=500)


class TopupRequestOut(BaseModel):
    model_config = {"from_attributes": True}

    topup_request_uuid: UUID
    account_uuid: UUID
    amount_kop: int
    proof_document_uuid: UUID
    payment_details: str | None
    status: str
    reject_reason: str | None
    reviewed_at: datetime | None
    created_at: datetime


class TopupResolveIn(BaseModel):
    action: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=500)


class PayoutOut(BaseModel):
    model_config = {"from_attributes": True}

    event_title: str
    company_name: str
    payout_uuid: UUID
    vacancy_uuid: UUID
    company_uuid: UUID
    workers_count: int
    amount_kop: int
    status: str
    created_at: datetime
    paid_at: datetime | None
