from uuid import UUID

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin
from app.core.ids import uuid7


class Filial(TimestampMixin, Base):
    __tablename__ = "filial"

    filial_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    company_uuid: Mapped[UUID] = mapped_column(ForeignKey("company.company_uuid"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(300))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
