from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationOut(BaseModel):
    model_config = {"from_attributes": True}

    notification_uuid: UUID
    kind: str
    title: str
    company_uuid: UUID | None
    vacancy_uuid: UUID | None
    read_at: datetime | None
    created_at: datetime


class NotificationListOut(BaseModel):
    unread: int
    items: list[NotificationOut]
