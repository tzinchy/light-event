from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class ServicePrice(TimestampMixin, Base):
    """Переопределение тарифа услуги админом (PLAN §11.6-B, §11.10-A).

    company_uuid = NULL — глобальный тариф; задан — тариф конкретной компании.
    Резолюция: компания → глобальный → дефолт из Settings (без seed — skill real-data-only).
    """

    __tablename__ = "service_price"
    __table_args__ = (UniqueConstraint("key", "company_uuid", name="uq_service_price_key_company"),)

    service_price_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    key: Mapped[str] = mapped_column(String(50), index=True)
    company_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("company.company_uuid"), index=True)
    amount_kop: Mapped[int] = mapped_column(BigInteger)
