import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, BigInteger, DateTime, Enum, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class TestKind(str, enum.Enum):
    platform = "platform"
    company = "company"


class TestStatus(str, enum.Enum):
    draft = "draft"
    pending_moderation = "pending_moderation"
    published = "published"
    rejected = "rejected"


class AttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    finished = "finished"
    abandoned = "abandoned"


class Test(TimestampMixin, Base):
    __tablename__ = "test"

    test_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    kind: Mapped[TestKind] = mapped_column(Enum(TestKind, native_enum=False, length=20))
    company_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("company.company_uuid"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    topic: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(1000))
    min_correct: Mapped[int]
    price_kop: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[TestStatus] = mapped_column(
        Enum(TestStatus, native_enum=False, length=20), default=TestStatus.draft, index=True
    )
    reject_reason: Mapped[str | None] = mapped_column(String(500))


class TestQuestion(TimestampMixin, Base):
    __tablename__ = "test_question"

    test_question_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    test_uuid: Mapped[UUID] = mapped_column(ForeignKey("test.test_uuid"), index=True)
    position: Mapped[int]
    text: Mapped[str] = mapped_column(String(500))
    multi: Mapped[bool] = mapped_column(default=False)
    options: Mapped[list[str]] = mapped_column(JSONB)
    # наружу не отдаётся: ответы уходят без correct_indices (PLAN §3.3)
    correct_indices: Mapped[list[int]] = mapped_column(ARRAY(Integer))


class TestAttempt(TimestampMixin, Base):
    __tablename__ = "test_attempt"

    test_attempt_uuid: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    test_uuid: Mapped[UUID] = mapped_column(ForeignKey("test.test_uuid"), index=True)
    user_uuid: Mapped[UUID] = mapped_column(ForeignKey("user.user_uuid"), index=True)
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, native_enum=False, length=20), default=AttemptStatus.in_progress
    )
    # ответы {test_question_uuid: [индексы]} — отдельная таблица не нужна (PLAN §3.3)
    answers: Mapped[dict] = mapped_column(JSONB, default=dict)
    correct_count: Mapped[int] = mapped_column(default=0)
    score_pct: Mapped[int] = mapped_column(default=0)
    passed: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
