from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# сроки действия ссылки из референса: 24ч / 7д / 30д
INVITE_TTL: dict[str, timedelta] = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


class InviteCreateIn(BaseModel):
    # main_manager через инвайт не выдаётся — владелец кабинета один
    role: Literal["manager", "coordinator", "staff"]
    expires_in: Literal["24h", "7d", "30d"]
    max_uses: int = Field(ge=1, le=1000)
    filial_uuid: UUID | None = None


class InviteOut(BaseModel):
    model_config = {"from_attributes": True}

    invite_link_uuid: UUID
    code: str
    role: str
    filial_uuid: UUID | None
    expires_at: datetime
    max_uses: int
    uses_count: int
    active: bool
