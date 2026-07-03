import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class ComplaintSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ComplaintStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"


class ComplaintTargetType(str, enum.Enum):
    user = "user"
    company = "company"


class Complaint(TimestampMixin, Base):
    """Жалоба участника (PLAN §3.7): свободный вид («Задержка оплаты», «Неявка на смену»…)."""

    __tablename__ = "complaint"

    complaint_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    author_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    target_type: Mapped[ComplaintTargetType] = mapped_column(
        Enum(ComplaintTargetType, native_enum=False, length=20)
    )
    target_uuid: Mapped[UUID] = mapped_column(index=True)
    vacancy_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("vacancy.vacancy_uuid"))
    kind: Mapped[str] = mapped_column(String(120))
    severity: Mapped[ComplaintSeverity] = mapped_column(
        Enum(ComplaintSeverity, native_enum=False, length=10)
    )
    text: Mapped[str] = mapped_column(String(2000))
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, native_enum=False, length=10), default=ComplaintStatus.open
    )
    resolution: Mapped[str | None] = mapped_column(String(1000))
    resolved_by_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("user.user_uuid"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
