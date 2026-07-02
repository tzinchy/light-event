import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.ids import uuid7


class CompanyStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"


class Company(Base):
    __tablename__ = "company"

    company_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, native_enum=False, length=20), default=CompanyStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
