from uuid import UUID

from sqlalchemy import BigInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class ServicePrice(TimestampMixin, Base):
    """Переопределение тарифа услуги админом (PLAN §11.6-B).

    Нет строки → действует дефолт из Settings; поэтому без seed (skill real-data-only).
    """

    __tablename__ = "service_price"

    service_price_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    amount_kop: Mapped[int] = mapped_column(BigInteger)
