from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ThreadOpenIn(BaseModel):
    application_uuid: UUID


class MessageSendIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Сообщение не может быть пустым")
        return value.strip()


class MessageOut(BaseModel):
    model_config = {"from_attributes": True}

    chat_message_uuid: UUID
    chat_thread_uuid: UUID
    sender_uuid: UUID
    text: str
    sent_at: datetime
    read_at: datetime | None


class ThreadOut(BaseModel):
    chat_thread_uuid: UUID
    application_uuid: UUID
    vacancy_uuid: UUID
    event_title: str
    role_name: str
    company_name: str
    counterpart_name: str | None
    unread_count: int
    last_message: MessageOut | None
