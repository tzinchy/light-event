from datetime import date, datetime, timezone
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Computed, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, MappedColumn

from src.database.core import Base


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    INVITED = "invited"


class UserAccountStatus(StrEnum):
    BASE = "base"
    PREMIUM = "premium"


class MedCardType(StrEnum):
    BASE = "base"
    FOOD = "food"


class Role(StrEnum):
    ADMIN = "admin"
    MAIN_MANAGER = "main_manager"
    MANAGER = "manager"
    CANDIDATE = "candidate"


class MedCard(Base):
    __tablename__ = "med_cards"
    med_card_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    medcard_name: Mapped[str] = MappedColumn(String, nullable=False)
    med_card_type: Mapped[MedCardType] = MappedColumn(String, nullable=False)


class User(Base):
    __tablename__ = "users"
    user_uuid: Mapped[UUID] = MappedColumn(PG_UUID, primary_key=True)
    username: Mapped[str] = MappedColumn(String, nullable=True, unique=True)
    password: Mapped[str] = MappedColumn(String, nullable=False)
    first_name: Mapped[str] = MappedColumn(String, nullable=False)
    middle_name: Mapped[str | None] = MappedColumn(String, nullable=True)
    last_name: Mapped[str] = MappedColumn(String, nullable=False)
    email: Mapped[str | None] = MappedColumn(String, nullable=True)
    phone_number: Mapped[str] = MappedColumn(String, nullable=False)
    city: Mapped[str] = MappedColumn(String, nullable=False)
    sex: Mapped[Sex] = MappedColumn(String, nullable=False)
    birth_date: Mapped[date] = MappedColumn(String, nullable=False)
    languages: Mapped[dict | None] = MappedColumn(JSONB, nullable=True)
    user_status: Mapped[UserStatus] = MappedColumn(
        String, nullable=False, default=UserStatus.ACTIVE
    )
    user_account_status: Mapped[UserAccountStatus] = MappedColumn(
        String, nullable=False, default=UserAccountStatus.BASE
    )
    user_roles: Mapped[Role] = MappedColumn(
        String, nullable=False, default=Role.CANDIDATE
    )
    telegram_tag: Mapped[str | None] = MappedColumn(String, nullable=True)
    telegram_link: Mapped[str | None] = MappedColumn(
        Computed(f"https://t.me/{telegram_tag}"), nullable=True
    )


class UserMedCard(Base):
    __tablename__ = "user_med_cards"
    user_med_card_id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    user_uuid: Mapped[UUID] = MappedColumn(
        PG_UUID, ForeignKey("users.user_uuid"), nullable=False
    )
    med_card_id: Mapped[int] = MappedColumn(
        Integer, ForeignKey("med_cards.med_card_id"), nullable=False
    )
    med_card_created: Mapped[date] = MappedColumn(
        Date, nullable=False, default=datetime.now(timezone.utc)
    )
