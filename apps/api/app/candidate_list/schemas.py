from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CandidateEntryIn(BaseModel):
    list: Literal["shortlist", "reserve", "blacklist"]
    note: str | None = Field(default=None, max_length=300)


class CandidateEntryOut(BaseModel):
    model_config = {"from_attributes": True}

    entry_uuid: UUID
    company_uuid: UUID
    user_uuid: UUID
    list: str
    note: str | None
    created_at: datetime
