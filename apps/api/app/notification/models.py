from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Notification(TimestampMixin, Base):
    """Уведомление пользователю (PLAN §11.8): напр. новая смена в избранной компании."""

    __tablename__ = "notification"

    notification_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    user_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(300))
    company_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("company.company_uuid"))
    vacancy_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("vacancy.vacancy_uuid"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
