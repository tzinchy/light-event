import enum
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class EmailKind(str, enum.Enum):
    otp = "otp"
    admin = "admin"


class EmailStatus(str, enum.Enum):
    sent = "sent"
    failed = "failed"


class EmailMessageLog(TimestampMixin, Base):
    """Журнал исходящих писем (PLAN §11.14): каждый OTP и каждое письмо админа."""

    __tablename__ = "email_message"

    email_message_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    to_email: Mapped[str] = mapped_column(String(320), index=True)
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20))  # EmailKind
    status: Mapped[str] = mapped_column(String(20))  # EmailStatus
    error: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("user.user_uuid"))
