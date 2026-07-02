import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin
from app.core.ids import uuid7


class ApplicationStatus(str, enum.Enum):
    review = "review"
    confirmed = "confirmed"
    reserve = "reserve"
    paid = "paid"
    done = "done"


class ApplicationEventKind(str, enum.Enum):
    """Ровно 4 шага таймлайна из референса: Отклик → Подтверждение → Смена → Выплата."""

    applied = "applied"
    confirmed = "confirmed"
    shift = "shift"
    payout = "payout"


class Application(TimestampMixin, Base):
    __tablename__ = "application"
    __table_args__ = (UniqueConstraint("vacancy_uuid", "user_uuid", name="uq_application_vacancy_user"),)

    application_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    vacancy_uuid: Mapped[UUID] = mapped_column(ForeignKey("vacancy.vacancy_uuid"), index=True)
    user_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=20), default=ApplicationStatus.review
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApplicationEvent(Base):
    """Событие таймлайна — факт, а не запись с жизненным циклом: только occurred_at."""

    __tablename__ = "application_event"

    application_event_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    application_uuid: Mapped[UUID] = mapped_column(ForeignKey("application.application_uuid"), index=True)
    kind: Mapped[ApplicationEventKind] = mapped_column(Enum(ApplicationEventKind, native_enum=False, length=20))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("user.user_uuid"))
