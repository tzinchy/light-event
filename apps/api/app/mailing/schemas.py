from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailSendIn(BaseModel):
    to_email: EmailStr
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=10_000)


class EmailMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_message_uuid: UUID
    to_email: str
    subject: str
    body: str
    kind: str
    status: str
    error: str | None
    created_by: UUID | None
    created_at: datetime
