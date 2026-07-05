from uuid import UUID

from sqlalchemy import BigInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class PaymentAccount(TimestampMixin, Base):
    """Счёт платформы для приёма пополнений (PLAN §11.9): реквизиты + месячный лимит оборота.

    Приоритетный счёт (`is_priority`) — с него начинается подбор при создании заявки; один на всех.
    """

    __tablename__ = "payment_account"

    payment_account_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    name: Mapped[str] = mapped_column(String(200))
    requisites: Mapped[str] = mapped_column(String(1000))
    monthly_limit_kop: Mapped[int] = mapped_column(BigInteger)
    is_priority: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)
