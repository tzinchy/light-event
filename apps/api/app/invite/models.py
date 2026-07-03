from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin
from app.team.models import CompanyRole


class InviteLink(TimestampMixin, Base):
    __tablename__ = "invite_link"

    invite_link_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    company_uuid: Mapped[UUID] = mapped_column(ForeignKey("company.company_uuid"), index=True)
    filial_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("filial.filial_uuid"))  # None = все филиалы
    company_role: Mapped[CompanyRole] = mapped_column(Enum(CompanyRole, native_enum=False, length=20))
    code: Mapped[str] = mapped_column(String(32), unique=True)  # light-event.app/join/<code>
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    max_uses: Mapped[int]
    uses_count: Mapped[int] = mapped_column(default=0)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_uuid: Mapped[UUID] = mapped_column(ForeignKey("team_member.team_member_uuid"))

    @property
    def active(self) -> bool:
        return (
            self.revoked_at is None
            and self.uses_count < self.max_uses
            and self.expires_at > datetime.now(UTC)
        )

    @property
    def role(self) -> CompanyRole:
        return self.company_role
