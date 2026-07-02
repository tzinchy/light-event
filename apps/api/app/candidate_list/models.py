import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin
from app.core.ids import uuid7


class CandidateList(str, enum.Enum):
    shortlist = "shortlist"
    reserve = "reserve"
    blacklist = "blacklist"


class CandidateListEntry(TimestampMixin, Base):
    """Кандидат состоит максимум в одном списке компании; ЧС скрывает его отклики от компании."""

    __tablename__ = "candidate_list_entry"
    __table_args__ = (UniqueConstraint("company_uuid", "user_uuid", name="uq_candidate_entry_company_user"),)

    entry_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    company_uuid: Mapped[UUID] = mapped_column(ForeignKey("company.company_uuid"), index=True)
    user_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    list: Mapped[CandidateList] = mapped_column(Enum(CandidateList, native_enum=False, length=20))
    note: Mapped[str | None] = mapped_column(String(300))
