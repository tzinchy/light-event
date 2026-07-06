import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, DateTime, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class PlatformRole(str, enum.Enum):
    user = "user"
    vip_user = "vip_user"
    admin = "admin"


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
    pd_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)
