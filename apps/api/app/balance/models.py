import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin
from app.core.ids import uuid7

# счёт платформы (owner_type=platform) один; фиксированный owner_uuid держит уникальность (owner_type, owner_uuid)
PLATFORM_OWNER_UUID = UUID(int=0)


class AccountOwnerType(str, enum.Enum):
    company = "company"
    user = "user"
    platform = "platform"


class LedgerKind(str, enum.Enum):
    topup = "topup"
    vacancy_fee = "vacancy_fee"
    test_fee = "test_fee"
    hold = "hold"
    release = "release"
    payout = "payout"
    commission = "commission"


class TopupStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Account(TimestampMixin, Base):
    __tablename__ = "account"
    __table_args__ = (UniqueConstraint("owner_type", "owner_uuid", name="uq_account_owner"),)

    account_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    owner_type: Mapped[AccountOwnerType] = mapped_column(Enum(AccountOwnerType, native_enum=False, length=20))
    owner_uuid: Mapped[UUID] = mapped_column(index=True)
    # денормализованный кэш поверх ledger_entry, сверяется в тестах (skill money-ledger)
    available_kop: Mapped[int] = mapped_column(BigInteger, default=0)
    on_hold_kop: Mapped[int] = mapped_column(BigInteger, default=0)

    @property
    def total_kop(self) -> int:
        return self.available_kop + self.on_hold_kop


class LedgerEntry(Base):
    """Журнал двойной записи. Append-only (без updated_at): сервисный слой не даёт UPDATE/DELETE."""

    __tablename__ = "ledger_entry"
    __table_args__ = (
        CheckConstraint("amount_kop > 0", name="amount_positive"),
        CheckConstraint("debit_account_uuid <> credit_account_uuid", name="different_accounts"),
    )

    ledger_entry_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    debit_account_uuid: Mapped[UUID] = mapped_column(ForeignKey("account.account_uuid"), index=True)
    credit_account_uuid: Mapped[UUID] = mapped_column(ForeignKey("account.account_uuid"), index=True)
    amount_kop: Mapped[int] = mapped_column(BigInteger)
    kind: Mapped[LedgerKind] = mapped_column(Enum(LedgerKind, native_enum=False, length=20))
    ref_type: Mapped[str | None] = mapped_column(String(40))
    ref_uuid: Mapped[UUID | None]
    comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TopupRequest(TimestampMixin, Base):
    __tablename__ = "topup_request"

    topup_request_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    account_uuid: Mapped[UUID] = mapped_column(ForeignKey("account.account_uuid"), index=True)
    amount_kop: Mapped[int] = mapped_column(BigInteger)
    proof_document_uuid: Mapped[UUID] = mapped_column(ForeignKey("document.document_uuid"))
    payment_details: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[TopupStatus] = mapped_column(
        Enum(TopupStatus, native_enum=False, length=20), default=TopupStatus.pending
    )
    reviewed_by_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("user.user_uuid"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reject_reason: Mapped[str | None] = mapped_column(String(500))
