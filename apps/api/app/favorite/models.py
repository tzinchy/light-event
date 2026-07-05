from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class CompanyFavorite(TimestampMixin, Base):
    """Пользователь подписан на компанию — чтобы получать уведомления о новых сменах (PLAN §11.8)."""

    __tablename__ = "company_favorite"
    __table_args__ = (UniqueConstraint("user_uuid", "company_uuid", name="uq_favorite_user_company"),)

    company_favorite_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    user_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    company_uuid: Mapped[UUID] = mapped_column(ForeignKey("company.company_uuid"), index=True)
