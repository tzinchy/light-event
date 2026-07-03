import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class CompanyStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class Company(TimestampMixin, Base):
    __tablename__ = "company"

    company_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    inn: Mapped[str] = mapped_column(String(12))
    ogrn: Mapped[str] = mapped_column(String(15))
    address: Mapped[str] = mapped_column(String(300))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    contact_phone: Mapped[str] = mapped_column(String(16))
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, native_enum=False, length=20), default=CompanyStatus.pending
    )
    reject_reason: Mapped[str | None] = mapped_column(String(500))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
