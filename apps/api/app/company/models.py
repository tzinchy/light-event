import enum
from uuid import UUID

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin
from app.core.ids import uuid7


class CompanyStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"


class Company(TimestampMixin, Base):
    __tablename__ = "company"

    company_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, native_enum=False, length=20), default=CompanyStatus.pending
    )
