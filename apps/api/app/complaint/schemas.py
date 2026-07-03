from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ComplaintCreateIn(BaseModel):
    target_type: Literal["user", "company"]
    target_uuid: UUID
    vacancy_uuid: UUID | None = None
    kind: str = Field(min_length=3, max_length=120)
    severity: Literal["low", "medium", "high"]
    text: str = Field(min_length=3, max_length=2000)


class ComplaintResolveIn(BaseModel):
    action: Literal["resolved", "dismissed"]
    resolution: str = Field(min_length=3, max_length=1000)


class ComplaintOut(BaseModel):
    model_config = {"from_attributes": True}

    complaint_uuid: UUID
    author_uuid: UUID
    target_type: str
    target_uuid: UUID
    vacancy_uuid: UUID | None
    kind: str
    severity: str
    text: str
    status: str
    resolution: str | None
    created_at: datetime
    resolved_at: datetime | None
