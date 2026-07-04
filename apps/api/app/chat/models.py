from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class ChatThread(TimestampMixin, Base):
    """Тред на заявку (PLAN §3.6): соискатель ↔ команда компании."""

    __tablename__ = "chat_thread"
    __table_args__ = (UniqueConstraint("application_uuid", name="uq_chat_thread_application"),)

    chat_thread_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    application_uuid: Mapped[UUID] = mapped_column(ForeignKey("application.application_uuid"), index=True)


class ChatMessage(Base):
    """Сообщение — факт: sent_at вместо created/updated, read_at по прочтении получателем."""

    __tablename__ = "chat_message"

    chat_message_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    chat_thread_uuid: Mapped[UUID] = mapped_column(ForeignKey("chat_thread.chat_thread_uuid"), index=True)
    sender_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    text: Mapped[str] = mapped_column(String(2000))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
