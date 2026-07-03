import enum
from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class ReviewKind(str, enum.Enum):
    about_org = "about_org"
    about_event = "about_event"
    about_worker = "about_worker"


class ReviewTargetType(str, enum.Enum):
    user = "user"
    company = "company"


class Review(TimestampMixin, Base):
    """Отзыв по завершённой заявке; один на пару (автор, заявка) — PLAN §3.7."""

    __tablename__ = "review"
    __table_args__ = (
        UniqueConstraint("author_uuid", "application_uuid", name="uq_review_author_application"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
    )

    review_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    application_uuid: Mapped[UUID] = mapped_column(ForeignKey("application.application_uuid"), index=True)
    vacancy_uuid: Mapped[UUID] = mapped_column(ForeignKey("vacancy.vacancy_uuid"), index=True)
    author_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    target_type: Mapped[ReviewTargetType] = mapped_column(
        Enum(ReviewTargetType, native_enum=False, length=20)
    )
    target_uuid: Mapped[UUID] = mapped_column(index=True)
    rating: Mapped[int]
    text: Mapped[str | None] = mapped_column(String(1000))
    kind: Mapped[ReviewKind] = mapped_column(Enum(ReviewKind, native_enum=False, length=20))
