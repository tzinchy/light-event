import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CompanyApplication(TimestampMixin, Base):
    """Заявка на подключение отеля от анонима (PLAN §11.16).

    Заявитель ещё без учётной записи — контакт хранится здесь; на approve
    заводится Company + User(main_manager). Пруф должности лежит в Storage.
    """

    __tablename__ = "company_application"

    company_application_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    # данные компании (как в CompanyCreateIn)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    inn: Mapped[str] = mapped_column(String(12))
    ogrn: Mapped[str] = mapped_column(String(15))
    address: Mapped[str] = mapped_column(String(300))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    contact_phone: Mapped[str] = mapped_column(String(16))
    contact_name: Mapped[str] = mapped_column(String(200))
    contact_email: Mapped[str] = mapped_column(String(254))
    contact_position: Mapped[str] = mapped_column(String(120))
    # одноразовый токен на догрузку пруф-документа к своей заявке
    upload_token: Mapped[str] = mapped_column(String(64))
    proof_storage_key: Mapped[str | None] = mapped_column(String(255))
    proof_mime: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=20),
        default=ApplicationStatus.pending,
        server_default=ApplicationStatus.pending.value,
    )
    reject_reason: Mapped[str | None] = mapped_column(String(500))
    # заполняется на approve — созданная компания
    company_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("company.company_uuid"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
