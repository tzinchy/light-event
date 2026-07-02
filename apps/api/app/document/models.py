import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.ids import uuid7


class DocumentKind(str, enum.Enum):
    passport = "passport"
    selfie_with_passport = "selfie_with_passport"
    medbook = "medbook"
    diploma = "diploma"
    payment_proof = "payment_proof"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class Document(Base):
    __tablename__ = "document"

    document_uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    owner_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    kind: Mapped[DocumentKind] = mapped_column(Enum(DocumentKind, native_enum=False, length=30))
    storage_key: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, length=20), default=DocumentStatus.pending
    )
    reject_reason: Mapped[str | None] = mapped_column(String(500))
    flag: Mapped[str | None] = mapped_column(String(120))
    reviewed_by_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("user.user_uuid"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
