import enum
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class PlatformRole(str, enum.Enum):
    user = "user"
    vip_user = "vip_user"
    admin = "admin"


class ModerationStatus(str, enum.Enum):
    pending = "pending"  # документы на проверке
    approved = "approved"  # админ подтвердил
    resubmit = "resubmit"  # нужно дослать документ
    banned = "banned"  # заблокирован (is_active=False)


class User(TimestampMixin, Base):
    __tablename__ = "user"

    user_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    phone: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True, index=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    name: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    platform_role: Mapped[PlatformRole] = mapped_column(
        Enum(PlatformRole, native_enum=False, length=20), default=PlatformRole.user
    )
    desired_roles: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list, server_default="{}")
    # опыт работы: none | up_to_1y | y1_3 | y3_6 (PLAN §3.1)
    experience: Mapped[str | None] = mapped_column(String(20))
    about: Mapped[str | None] = mapped_column(String(2000))  # «О себе»
    # английский: none | basic | intermediate | advanced | fluent
    english_level: Mapped[str | None] = mapped_column(String(20))
    # образование: secondary | vocational | higher
    education: Mapped[str | None] = mapped_column(String(20))
    telegram: Mapped[str | None] = mapped_column(String(64))  # тег без @; контакт — наружу не отдаём
    birth_date: Mapped[date | None] = mapped_column(Date)
    citizenship: Mapped[str | None] = mapped_column(String(100))
    gender: Mapped[str | None] = mapped_column(String(10))  # male | female
    pd_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)
    # модерация пользователя (PLAN §11.15) — отдельно от per-document document.status
    moderation_status: Mapped[ModerationStatus] = mapped_column(
        Enum(ModerationStatus, native_enum=False, length=20),
        default=ModerationStatus.pending,
        server_default=ModerationStatus.pending.value,
    )
    moderation_reason: Mapped[str | None] = mapped_column(String(500))
    moderated_by_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("user.user_uuid"))
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
