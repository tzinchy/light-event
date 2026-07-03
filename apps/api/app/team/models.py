import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class CompanyRole(str, enum.Enum):
    main_manager = "main_manager"
    manager = "manager"
    coordinator = "coordinator"
    staff = "staff"


class TeamMember(TimestampMixin, Base):
    __tablename__ = "team_member"
    __table_args__ = (UniqueConstraint("user_uuid", "company_uuid", name="uq_team_member_user_company"),)

    team_member_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    user_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    company_uuid: Mapped[UUID] = mapped_column(ForeignKey("company.company_uuid"), index=True)
    filial_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("filial.filial_uuid"))  # None = все филиалы
    company_role: Mapped[CompanyRole] = mapped_column(Enum(CompanyRole, native_enum=False, length=20))
    # матрица прав (skill rbac-permissions); у main_manager всегда полный доступ
    perm_create: Mapped[bool] = mapped_column(default=False)
    perm_hire: Mapped[bool] = mapped_column(default=False)
    perm_finance: Mapped[bool] = mapped_column(default=False)
    perm_invite: Mapped[bool] = mapped_column(default=False)
    email: Mapped[str | None] = mapped_column(String(254))

    def has_permission(self, perm: str) -> bool:
        if self.company_role == CompanyRole.main_manager:
            return True
        return bool(getattr(self, f"perm_{perm}"))
