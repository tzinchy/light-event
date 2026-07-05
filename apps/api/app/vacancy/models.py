import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, BigInteger, DateTime, Enum, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class VacancyStatus(str, enum.Enum):
    draft = "draft"
    pending_moderation = "pending_moderation"
    active = "active"
    rejected = "rejected"
    done = "done"


class Vacancy(TimestampMixin, Base):
    __tablename__ = "vacancy"

    vacancy_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    company_uuid: Mapped[UUID] = mapped_column(ForeignKey("company.company_uuid"), index=True)
    filial_uuid: Mapped[UUID] = mapped_column(ForeignKey("filial.filial_uuid"))
    created_by_uuid: Mapped[UUID] = mapped_column(ForeignKey("team_member.team_member_uuid"))
    role_name: Mapped[str] = mapped_column(String(80))
    event_title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))  # свободный текст «О событии»
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    venue_address: Mapped[str] = mapped_column(String(300))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    pay_hour_kop: Mapped[int] = mapped_column(BigInteger)
    pay_total_kop: Mapped[int] = mapped_column(BigInteger)  # пересчитывается сервисом из ставки и длительности
    slots: Mapped[int]
    urgent: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list, server_default="{}")
    requirements: Mapped[list[str]] = mapped_column(ARRAY(String(120)), default=list, server_default="{}")
    # обязательные тесты: откликнуться может только прошедший все (PLAN §11.6-D); пусто = без ограничений
    required_test_uuids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PgUUID(as_uuid=True)), default=list, server_default="{}"
    )
    status: Mapped[VacancyStatus] = mapped_column(
        Enum(VacancyStatus, native_enum=False, length=20), default=VacancyStatus.draft, index=True
    )
    reject_reason: Mapped[str | None] = mapped_column(String(500))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
