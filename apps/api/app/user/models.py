import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin
from app.core.ids import uuid7


class PlatformRole(str, enum.Enum):
    user = "user"
    vip_user = "vip_user"
    admin = "admin"


class User(TimestampMixin, Base):
    __tablename__ = "user"

    user_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    phone: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    platform_role: Mapped[PlatformRole] = mapped_column(
        Enum(PlatformRole, native_enum=False, length=20), default=PlatformRole.user
    )
    desired_roles: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list, server_default="{}")
    pd_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)
